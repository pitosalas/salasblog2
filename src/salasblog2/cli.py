#!/usr/bin/env python3
# cli — Local dev CLI: generate/server/reset/deploy/sync-raindrops commands
# Author: Pito Salas and Claude Code
# Version: 7
# Created: 2026-09-09
# Updated: 2026-10-20
# Open Source Under MIT license
"""
Unified CLI for Salasblog2 - Static site generator with Raindrop.io integration.
"""

import argparse
import json
import os
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

from salasblog2.generator import SiteGenerator
from salasblog2.legacy_commands import (
    URL_MAP_FILE,
    WAYBACK_CACHE_FILE,
    build_map,
    content_dirs,
    load_url_map,
    redirect_targets,
    rewrite_content,
    summarize_map,
)
from salasblog2.link_check import find_dead_self_links
from salasblog2.raindrop import RaindropDownloader
from salasblog2.tag_cleanup import proposals_to_json, summaries_to_json, summarize_post
from salasblog2.tag_conversion import (
    apply_tag_decisions,
    convert_blog_tags,
    convert_directory,
    select_generic_posts,
)
from salasblog2.tag_vocabulary import TAG_HINTS_FILE, canonicalize_tags
from salasblog2.utils import load_curated_tag_aliases, remove_frontmatter_key
from salasblog2.wp_media import extract_media, rewrite_media_content, url_status
from salasblog2.wp_taxonomy import (
    MERGES_FILE,
    build_wp_proposals,
    index_local_posts,
    load_merges,
    match_posts,
    parse_wxr,
)

load_dotenv()


def cmd_generate(args):
    """Generate the static site"""
    generator = SiteGenerator()
    generator.generate_site()


def cmd_reset(args):
    """Delete all generated files"""
    generator = SiteGenerator()
    generator.reset_output()


def cmd_deploy(args):
    """Deploy site to Fly.io"""
    generator = SiteGenerator()
    generator.deploy_to_fly()


def cmd_sync_raindrops(args):
    """Download new bookmarks from Raindrop.io"""
    downloader = RaindropDownloader()
    downloader.download_raindrops(
        reset=args.reset, count=args.count, rebuild_cache=args.rebuild_cache
    )


def cmd_legacy_map(args):
    """Build the reviewed legacy URL map from content links"""
    url_map = build_map(Path(args.content), URL_MAP_FILE, WAYBACK_CACHE_FILE)
    print(summarize_map(url_map))
    print(f"wrote {URL_MAP_FILE}")


def cmd_legacy_rewrite(args):
    """Rewrite mapped legacy links in content (dry run unless --apply)"""
    rewrite_content(Path(args.content), URL_MAP_FILE, is_dry_run=not args.apply)


def cmd_check_links(args):
    """Report self-links in content that resolve to nothing"""
    redirects = redirect_targets(load_url_map(URL_MAP_FILE))
    dead = find_dead_self_links(
        content_dirs(Path(args.content)), Path(args.output), redirects
    )
    for link in dead:
        print(f"{link.source_file}: {link.url}")
    print(f"{len(dead)} dead self-links")


def cmd_wp_media(args):
    """Self-host WordPress-era images and repair the post links to them"""
    media_dir = Path(args.media_dir)
    if args.extract:
        count = extract_media(Path(args.extract), media_dir)
        print(f"extracted {count} files into {media_dir}")
        return
    unmatched = rewrite_media_content(
        content_dirs(Path(args.content)), media_dir, is_dry_run=not args.apply
    )
    if args.report:
        for url in sorted(set(unmatched)):
            print(f"{url_status(url)}  {url}")


def cmd_wp_tags(args):
    """Write curated-tag proposals from WordPress terms"""
    wp_posts = parse_wxr(Path(args.wxr))
    merges = load_merges(MERGES_FILE)
    tag_hints = Path(args.tag_hints)
    blog_dir = Path(args.content) / "blog"
    matched, unmatched = match_posts(wp_posts, *index_local_posts(blog_dir))
    proposals = build_wp_proposals(blog_dir, matched, merges, tag_hints)
    Path(args.out).write_text(proposals_to_json(proposals), encoding="utf-8")
    gained = Counter(
        tag for p in proposals for tag in set(p.proposed_tags) - set(p.current_tags)
    )
    print(f"matched {len(matched)} posts, {len(unmatched)} unmatched")
    print(f"{len(proposals)} posts gain tags; wrote {args.out}")
    for tag, count in gained.most_common():
        print(f"  {count:5} {tag}")


def cmd_strip_categories(args):
    """Remove the retired `category:` line from post and page frontmatter"""
    changed = 0
    for content_dir in content_dirs(Path(args.content)):
        for md_file in sorted(content_dir.glob("*.md")):
            text = md_file.read_bytes().decode("utf-8")
            new_text = remove_frontmatter_key(text, "category")
            if new_text == text:
                continue
            changed += 1
            if args.apply:
                md_file.write_bytes(new_text.encode("utf-8"))
    action = "stripped" if args.apply else "would strip"
    print(f"{action} category from {changed} files")


def cmd_convert_tags(args):
    """Convert existing raindrop and blog tags onto the curated list, in place"""
    alias_map = load_curated_tag_aliases(TAG_HINTS_FILE)
    content_root = Path(args.content)
    action = "changed" if args.apply else "would change"
    for subdir, convert in (
        ("raindrops", canonicalize_tags),
        ("blog", convert_blog_tags),
    ):
        report = convert_directory(
            content_root / subdir, convert, alias_map, args.apply
        )
        print(
            f"{subdir}: {action} {report.files_changed} files, "
            f"{report.tags_kept} tags kept, {sum(report.dropped.values())} dropped, "
            f"{report.now_untagged} now untagged"
        )
        for tag, count in report.dropped.most_common(args.top_dropped):
            print(f"  {count:5} {tag}")


def cmd_generic_tags(args):
    """Select posts still carrying a generic tag, or apply tag decisions"""
    blog_dir = Path(args.content) / "blog"
    if args.decisions:
        decisions = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
        alias_map = load_curated_tag_aliases(TAG_HINTS_FILE)
        changed = apply_tag_decisions(blog_dir, decisions, alias_map, args.apply)
        print(f"{'changed' if args.apply else 'would change'} {len(changed)} posts")
        return
    posts = select_generic_posts(blog_dir, args.tag, args.limit)
    summaries = [summarize_post(path) for path in posts]
    Path(args.out).write_text(summaries_to_json(summaries), encoding="utf-8")
    print(f"selected {len(posts)} posts tagged {args.tag!r}; wrote {args.out}")


def cmd_server(args):
    """Start the FastAPI server"""
    import uvicorn

    print(f"🚀 Starting server on http://localhost:{args.port}")
    if args.reload:
        uvicorn.run(
            "salasblog2.server:app", host="0.0.0.0", port=args.port, reload=True
        )
    else:
        from salasblog2.server import app

        uvicorn.run(app, host="0.0.0.0", port=args.port)


def cmd_help(args):
    """Show help message"""
    print("salasblog2 - Static site generator with Raindrop.io integration")
    print()
    print("Commands:")
    print("  generate           - Process markdown files and generate static HTML site")
    print(
        "  server             - Start FastAPI server to serve site with API endpoints"
    )
    print("  reset              - Delete all generated files")
    print("  deploy             - Deploy site to Fly.io")
    print(
        "  sync-raindrops     - Download new bookmarks from Raindrop.io (for link blog)"
    )
    print("  legacy-map         - Build 02-doc/legacy-url-map.json from legacy links")
    print("  legacy-rewrite     - Rewrite mapped legacy links (dry run unless --apply)")
    print("  check-links        - Report self-links that resolve to nothing")
    print("  wp-media           - Self-host WordPress images, repair links (--apply)")
    print("  wp-tags            - WordPress terms -> curated tag proposals")
    print(
        "  strip-categories   - Remove retired category lines (dry run unless --apply)"
    )
    print(
        "  convert-tags       - Convert tags onto the curated list (dry run unless --apply)"
    )
    print("  generic-tags       - Select generic-tagged posts or apply tag decisions")
    print("  help               - Show this help message")
    print()
    print("Options:")
    print("  --port PORT        - Port for server (default: 8000)")
    print("  --reload           - Enable auto-reload for development (server command)")
    print("  --reset            - Reset link blog cache (for sync-raindrops command)")
    print(
        "  --rebuild-cache    - Rebuild cache from existing files (for sync-raindrops command)"
    )
    print(
        "  --count N          - Limit link blog download (for sync-raindrops command)"
    )


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Static site generator with Raindrop.io integration",
        add_help=False,  # We'll handle help ourselves
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate static site")
    generate_parser.set_defaults(func=cmd_generate)

    # Server command
    server_parser = subparsers.add_parser("server", help="Start FastAPI server")
    server_parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", 8000)),
        help="Port to run server on (default: PORT env var or 8000)",
    )
    server_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )
    server_parser.set_defaults(func=cmd_server)

    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Delete generated files")
    reset_parser.set_defaults(func=cmd_reset)

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy to Fly.io")
    deploy_parser.set_defaults(func=cmd_deploy)

    # Sync raindrops command
    sync_parser = subparsers.add_parser(
        "sync-raindrops", help="Download bookmarks from Raindrop.io for link blog"
    )
    sync_parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all existing link blog posts and rebuild from scratch",
    )
    sync_parser.add_argument(
        "--rebuild-cache",
        action="store_true",
        help="Rebuild cache from existing files (fixes duplicate detection)",
    )
    sync_parser.add_argument(
        "--count",
        type=int,
        metavar="N",
        help="Limit the number of link blog posts to download",
    )
    sync_parser.set_defaults(func=cmd_sync_raindrops)

    # Legacy link repair commands
    legacy_map_parser = subparsers.add_parser(
        "legacy-map", help="Build the legacy URL map"
    )
    legacy_map_parser.add_argument("--content", default="content", help="Content root")
    legacy_map_parser.set_defaults(func=cmd_legacy_map)

    rewrite_parser = subparsers.add_parser(
        "legacy-rewrite", help="Rewrite mapped legacy links in content"
    )
    rewrite_parser.add_argument("--content", default="content", help="Content root")
    rewrite_parser.add_argument(
        "--apply", action="store_true", help="Write changes (default: dry run)"
    )
    rewrite_parser.set_defaults(func=cmd_legacy_rewrite)

    check_parser = subparsers.add_parser(
        "check-links", help="Report dead self-links in content"
    )
    check_parser.add_argument("--content", default="content", help="Content root")
    check_parser.add_argument("--output", default="output", help="Generated site dir")
    check_parser.set_defaults(func=cmd_check_links)

    wp_media_parser = subparsers.add_parser(
        "wp-media", help="Self-host WordPress images and repair post links"
    )
    wp_media_parser.add_argument("--content", default="content", help="Content root")
    wp_media_parser.add_argument(
        "--media-dir", default="static/images/wp", help="Local media directory"
    )
    wp_media_parser.add_argument(
        "--extract", metavar="TAR", help="Copy the media tar into --media-dir"
    )
    wp_media_parser.add_argument(
        "--apply", action="store_true", help="Write changes (default: dry run)"
    )
    wp_media_parser.add_argument(
        "--report", action="store_true", help="HEAD-check unmatched URLs"
    )
    wp_media_parser.set_defaults(func=cmd_wp_media)

    wp_tags_parser = subparsers.add_parser(
        "wp-tags", help="Use WordPress categories/tags as a tag signal"
    )
    wp_tags_parser.add_argument("--wxr", required=True, help="WordPress export file")
    wp_tags_parser.add_argument("--content", default="content", help="Content root")
    wp_tags_parser.add_argument(
        "--tag-hints", default="02-doc/tag-hints.md", help="Curated tag list"
    )
    wp_tags_parser.add_argument(
        "--out", default="wp-tag-proposals.json", help="Proposals JSON to write"
    )
    wp_tags_parser.set_defaults(func=cmd_wp_tags)

    strip_parser = subparsers.add_parser(
        "strip-categories", help="Remove category lines from frontmatter"
    )
    strip_parser.add_argument("--content", default="content", help="Content root")
    strip_parser.add_argument(
        "--apply", action="store_true", help="Write changes (default: dry run)"
    )
    strip_parser.set_defaults(func=cmd_strip_categories)

    convert_tags_parser = subparsers.add_parser(
        "convert-tags", help="Convert raindrop and blog tags onto the curated list"
    )
    convert_tags_parser.add_argument(
        "--content", default="content", help="Content root"
    )
    convert_tags_parser.add_argument(
        "--apply", action="store_true", help="Write changes (default: dry run)"
    )
    convert_tags_parser.add_argument(
        "--top-dropped", type=int, default=20, help="Most-dropped tags to list"
    )
    convert_tags_parser.set_defaults(func=cmd_convert_tags)

    generic_parser = subparsers.add_parser(
        "generic-tags", help="Judgment pass for generic technology/personal tags"
    )
    generic_parser.add_argument("--content", default="content", help="Content root")
    generic_parser.add_argument(
        "--tag", default="technology", help="Generic tag to select posts by"
    )
    generic_parser.add_argument("--limit", type=int, default=50, help="Batch size")
    generic_parser.add_argument(
        "--out", default="generic-candidates.json", help="Summaries JSON to write"
    )
    generic_parser.add_argument(
        "--decisions", help="Decisions JSON [{filename, tags}] to apply instead"
    )
    generic_parser.add_argument(
        "--apply", action="store_true", help="Write decisions (default: dry run)"
    )
    generic_parser.set_defaults(func=cmd_generic_tags)

    # Help command
    help_parser = subparsers.add_parser("help", help="Show help message")
    help_parser.set_defaults(func=cmd_help)

    # Parse arguments
    args = parser.parse_args()

    # If no command specified, show help
    if not args.command:
        cmd_help(args)
        return

    # Execute the command
    args.func(args)


if __name__ == "__main__":
    main()
