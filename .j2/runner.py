#!/usr/bin/env python3
"""j2 runner — fills a workflow template with context from disk and prints to stdout."""
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

FOOTER = """
---
End your response with exactly these three lines, formatted with markdown bold labels to make them visually distinct (nothing after them):
\033[32mcompleted:\033[0m <one sentence: what was just done>
\033[33mstate:\033[0m <N> spec gaps | <N> features need tasks | <N> tasks pending   ← replace each <N> with an actual integer count
\033[36mnext:\033[0m <slash command — determined by this priority order:
  1. If spec gaps > 0 (previous run reported {{prev_spec_gaps}} gaps) → /refresh
  2. Else if not-done features lack task files ({{missing_tasks}}) → /tasks-gen <first listed>
  3. Else if any tasks are pending → /task-next
  4. Else (all features done, no pending tasks) → /features-update (to add new features) or /deploy (to ship)>

Also write these three lines to .j2/state.md (overwriting it), without ANSI codes and without the markdown bold.
"""


def load_config(root):
    # Read settings.yaml from the project's .j2/config directory.
    path = root / ".j2" / "config" / "settings.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def load_workflow(root):
    # Read workflow.yaml and return the list of step definitions.
    path = root / ".j2" / "config" / "workflow.yaml"
    with open(path) as f:
        return yaml.safe_load(f)["steps"]


def find_step(workflow, command_id):
    # Return the step dict matching command_id, or raise ValueError if not found.
    for step in workflow:
        if step["id"] == command_id:
            return step
    raise ValueError(
        f"Unknown command: {command_id!r}. "
        f"Valid commands: {[s['id'] for s in workflow]}"
    )


def load_template(root, settings, template_name):
    return (root / settings["j2"]["templates_dir"] / template_name).read_text()


def find_placeholders(template):
    return set(re.findall(r"\{\{(\w+)\}\}", template))


def load_spec(root, settings):
    # Concatenate all .md files in the specs directory, separated by horizontal rules.
    specs_dir = root / settings["j2"]["specs_dir"]
    parts = [f.read_text() for f in sorted(specs_dir.glob("*.md"))]
    if not parts:
        return "(no spec files found — add .md files to .j2/specs/ before running this command)"
    return "\n\n---\n\n".join(parts)


def load_features(root, settings):
    # Read and return the full features file.
    path = root / settings["j2"]["features_file"]
    return path.read_text()


def filter_done_features(features_text):
    # Strip done feature sections, replace with a count summary.
    sections = re.split(r"(?=^## F)", features_text, flags=re.MULTILINE)
    kept = []
    done_count = 0
    for section in sections:
        if section.startswith("## F") and re.search(r"\*\*Status\*\*:\s*done", section, re.IGNORECASE):
            done_count += 1
            continue
        kept.append(section)
    result = "".join(kept).rstrip()
    if done_count > 0:
        result += f"\n\n--- {done_count} completed features omitted ---\n"
    return result


def load_tasks(root, settings, feature_id):
    # Read and return the task file for a given feature ID; check done/ if not in active tasks.
    tasks_dir = root / settings["j2"]["tasks_dir"]
    active = tasks_dir / f"{feature_id}.md"
    archived = tasks_dir / "done" / f"{feature_id}.md"
    path = active if active.exists() else archived
    return path.read_text()


def extract_feature(features_text, feature_id):
    # Extract the markdown section for a single feature (e.g. ## F01 —) from the features file.
    pattern = rf"(^## {re.escape(feature_id.upper())}\b.*?)(?=^## |\Z)"
    match = re.search(pattern, features_text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError(f"Feature {feature_id.upper()!r} not found in features file.")
    return match.group(1).strip()


def extract_task(tasks_text, task_id):
    # Extract the markdown section for a single task (e.g. ### T01 —) from a task file.
    pattern = rf"(^### {re.escape(task_id.upper())}\b.*?)(?=^### |\Z)"
    match = re.search(pattern, tasks_text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError(f"Task {task_id.upper()!r} not found in tasks file.")
    return match.group(1).strip()


def prev_spec_gaps(root):
    # Read spec gap count from the last state.md; default to 0 if missing or unparseable.
    state_path = root / ".j2" / "state.md"
    try:
        match = re.search(r"(\d+)\s+spec gaps", state_path.read_text())
        return match.group(1) if match else "0"
    except FileNotFoundError:
        return "0"


def missing_tasks_summary(root, settings):
    # Return comma-separated not-done features missing task files, sorted by priority.
    priority_order = {"high": 0, "medium": 1, "low": 2}
    try:
        features_text = load_features(root, settings)
    except FileNotFoundError:
        return "none"
    tasks_dir = root / settings["j2"]["tasks_dir"]
    pattern = r"^## (F\d+) —.*?\n\*\*Priority\*\*: (\w+)\n\*\*Status\*\*: ([^\n|]+)"
    missing = []
    for fid, priority, status in re.findall(pattern, features_text, re.MULTILINE):
        if status.strip().lower() == "done":
            continue
        if not (tasks_dir / f"{fid}.md").exists() and not (tasks_dir / "done" / f"{fid}.md").exists():
            missing.append((priority_order.get(priority.lower(), 9), fid, priority))
    missing.sort()
    return ", ".join(f"{fid} ({pri})" for _, fid, pri in missing) or "none"


def find_default_feature(root, settings):
    # Return the first in-progress feature ID, or the first not-started feature ID.
    try:
        features_text = load_features(root, settings)
    except FileNotFoundError:
        return "F01"
    pattern = r"^## (F\d+) —.*?\n\*\*Priority\*\*: \w+\n\*\*Status\*\*: ([^\n|]+)"
    in_progress = None
    not_started = None
    for fid, status in re.findall(pattern, features_text, re.MULTILINE):
        s = status.strip().lower()
        if s == "in progress" and in_progress is None:
            in_progress = fid
        elif s == "not started" and not_started is None:
            not_started = fid
    return in_progress or not_started or "F01"


def compute_status(root, settings):
    # Compute and return the final formatted status text directly.
    specs_dir = root / ".j2" / "specs"
    spec_count = len(list(specs_dir.glob("*.md"))) if specs_dir.exists() else 0

    try:
        features_text = load_features(root, settings)
    except FileNotFoundError:
        features_text = ""

    pattern = r"^## (F\d+) —.*?\n\*\*Priority\*\*: \w+\n\*\*Status\*\*: ([^\n|]+)"
    counts = {"done": 0, "in progress": 0, "not started": 0}
    for _, status in re.findall(pattern, features_text, re.MULTILINE):
        s = status.strip().lower()
        if s in counts:
            counts[s] += 1

    missing = missing_tasks_summary(root, settings)

    tasks_dir = root / settings["j2"]["tasks_dir"]
    pending = 0
    if tasks_dir.exists():
        for tf in tasks_dir.glob("*.md"):
            pending += tf.read_text().count("**Status**: not started")

    state_path = root / ".j2" / "state.md"
    last_completed = next_cmd = "(unknown)"
    if state_path.exists():
        state_text = state_path.read_text()
        m = re.search(r"^completed:\s*(.+)", state_text, re.MULTILINE)
        if m:
            last_completed = m.group(1).strip()
        m = re.search(r"^next:\s*(.+)", state_text, re.MULTILINE)
        if m:
            next_cmd = m.group(1).strip()

    lines = [
        "Project Status",
        "==============",
        f"Specs:      {spec_count}",
        f"Features:   {counts['done']} done / {counts['in progress']} in progress / {counts['not started']} not started",
        f"Missing task files: {missing}",
        f"Pending tasks: {pending}",
        f"Last completed: {last_completed}",
        f"Next:       {next_cmd}",
    ]
    return "\n".join(lines)


def clean_export(root, target):
    # Copy the project to target, excluding all j2 infrastructure, then remove runner.py.
    target_path = Path(target).resolve()
    target_path.mkdir(parents=True, exist_ok=True)
    excludes = ["--exclude=.j2", "--exclude=scaffold", "--exclude=.claude", "--exclude=.coverage"]
    subprocess.run(
        ["rsync", "-a", *excludes, f"{root}/", f"{target_path}/"],
        check=True,
    )
    residual = target_path / "runner.py"
    if residual.exists():
        residual.unlink()
    return target_path


def fill_template(template, context):
    # Replace all {{key}} tokens in a single pass so substituted values are not re-scanned.
    def replacer(match):
        return context.get(match.group(1), match.group(0))
    return re.sub(r"\{\{(\w+)\}\}", replacer, template)


def build_context(root, settings, placeholders, args):
    # Load each context value needed by the template, based on which placeholders are present.
    loaders = {
        "spec":       lambda: load_spec(root, settings),
        "rules":      lambda: (root / settings["j2"]["rules_file"]).read_text(),
        "features":   lambda: filter_done_features(load_features(root, settings)),
        "feature":    lambda: extract_feature(load_features(root, settings), args.feature),
        "tasks":      lambda: load_tasks(root, settings, args.feature),
        "task":       lambda: extract_task(load_tasks(root, settings, args.feature), args.task),
        "feature_id":       lambda: args.feature if args.feature else find_default_feature(root, settings),
        "feature_arg_provided": lambda: "yes" if args.feature else "no",
        "request":          lambda: args.request,
        "target":           lambda: args.target,
        "default_feature":  lambda: find_default_feature(root, settings),
        "prev_spec_gaps": lambda: prev_spec_gaps(root),
        "missing_tasks":  lambda: missing_tasks_summary(root, settings),
        "state":          lambda: (root / ".j2" / "state.md").read_text(),
        "deploy_mode":    lambda: "dev-repo" if (root / "scaffold").is_dir() else "export",
    }
    context = {}
    for placeholder in placeholders:
        if placeholder not in loaders:
            print(f"Warning: no loader for placeholder {{{{{placeholder}}}}}", file=sys.stderr)
            continue
        try:
            context[placeholder] = loaders[placeholder]()
        except FileNotFoundError as e:
            context[placeholder] = f"(not yet available: {e.filename})"
    return context


def resolve_next_command(root, args):
    # Read state.md and rewrite args.command (and args.feature) from the `next:` line.
    state_path = root / ".j2" / "state.md"
    text = state_path.read_text()
    match = re.search(r"^next:\s+/(\S+)(?:\s+(\S+))?", text, re.MULTILINE)
    if not match:
        raise ValueError("No 'next:' line found in .j2/state.md")
    args.command = match.group(1)
    if match.group(2):
        args.feature = match.group(2)


def main():
    parser = argparse.ArgumentParser(description="j2 template runner")
    parser.add_argument("command", help="Workflow command ID (e.g. task-next), or 'continue' to read from state.md")
    parser.add_argument("--feature", default=None, help="Feature ID (e.g. F01)")
    parser.add_argument("--task", default=None, help="Task ID (e.g. T01)")
    parser.add_argument("--request", default=None, help="Refinement request text")
    parser.add_argument("--target", default=None, help="Target directory (for deploy)")
    parser.add_argument("--root", default=".", help="Project root directory (default: cwd)")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    try:
        if args.command == "continue":
            resolve_next_command(root, args)
        settings = load_config(root)
        if args.command == "status":
            print(compute_status(root, settings))
            return
        workflow = load_workflow(root)
        step = find_step(workflow, args.command)
        template = load_template(root, settings, step["template"])
        placeholders = find_placeholders(template)
        footer_placeholders = find_placeholders(FOOTER)
        context = build_context(root, settings, placeholders | footer_placeholders, args)
        print(fill_template(template, context) + fill_template(FOOTER, context))
    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
