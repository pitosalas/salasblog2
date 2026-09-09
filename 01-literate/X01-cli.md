---
version: "1.0"
generated: "2026-09-08"
---

# `cli.py` — The Local Command-Line Front Door

## What this module is for

`cli.py` is a thin `argparse`-based dispatcher that turns a handful of shell
commands (`generate`, `server`, `reset`, `deploy`, `sync-raindrops`, `help`)
into calls on the two objects that do the real work: `SiteGenerator` and
`RaindropDownloader`. It is the module a developer runs directly — `python
-m salasblog2.cli server --reload` or similar — when working on the blog
locally, as opposed to the `Makefile`/`uv` targets that wrap the same
commands for convenience during day-to-day development, and the Fly.io
container entrypoint that starts the server for production.

Three entry points, one implementation each. `Makefile` targets exist so a
developer doesn't have to remember `uv run python -m salasblog2.cli ...`;
Fly.io's container start command doesn't go through this file at all — it
imports `salasblog2.server:app` directly. `cli.py` is the layer in between:
a single, scriptable, human-friendly surface that both of those can (and in
the Makefile's case, do) call through, so the command-to-behavior mapping
lives in exactly one place rather than being duplicated across a Makefile
and a shell script.

## Commands as thin wrappers, not logic

Every `cmd_*` function follows the same shape: construct a `SiteGenerator`
or `RaindropDownloader`, call one method on it, done.

```python
def cmd_generate(args):
    """Generate the static site"""
    generator = SiteGenerator()
    generator.generate_site()
```

None of these functions contain business logic — that discipline is
deliberate. If `cli.py` started making decisions about *how* a site gets
generated or *when* raindrops get synced, that logic would only be
reachable from the command line, invisible to the FastAPI routes that also
need to trigger generation and syncing. Keeping every `cmd_*` a one-line
delegation means the CLI and the web server are just two callers of the
same underlying classes, never two implementations of the same behavior.

## `cmd_server`: two ways to start uvicorn

`cmd_server` is the one command with a real branch in it, and the branch
exists for a concrete reason — `uvicorn`'s `reload=True` mode requires an
*importable module string* (`"salasblog2.server:app"`) rather than an
already-constructed app object, because it needs to re-import the module
on every file change:

```python
if args.reload:
    uvicorn.run("salasblog2.server:app", host="0.0.0.0", port=args.port, reload=True)
else:
    from .server import app
    uvicorn.run(app, host="0.0.0.0", port=args.port)
```

Without `--reload`, the app object is imported once up front and handed to
`uvicorn.run()` directly — a simpler path with no re-import machinery,
appropriate for the common case of just running the server without editing
it live. The deferred `from .server import app` (inside the `else` branch
rather than at module top) also means importing `cli.py` doesn't pull in
the full server module unless the `server` command is actually used.

## `main()`: argparse subcommands, `func` dispatch

`main()` builds one `argparse` subparser per command and attaches the
handler via `set_defaults(func=cmd_x)`, so dispatch at the end is a single
line — `args.func(args)` — regardless of which command was chosen:

```python
generate_parser = subparsers.add_parser('generate', help='Generate static site')
generate_parser.set_defaults(func=cmd_generate)
```

`add_help=False` on the top-level parser is intentional: the module defines
its own `cmd_help`, printed both for an explicit `help` command and when no
command is given at all, so `salasblog2` with no arguments is friendly
rather than an argparse usage error. The trade-off is that this help text
is hand-maintained prose, separate from argparse's own `--help` output —
the two can drift if a flag is added to one subparser and not mentioned in
`cmd_help`'s manually written `Options:` block.

## A minor style-guide deviation

This module imports `SiteGenerator` and `RaindropDownloader` via relative
imports (`.generator`, `.raindrop`):

```python
from .generator import SiteGenerator
from .raindrop import RaindropDownloader
```

The project's style guide calls for absolute imports only. It's a small
inconsistency worth flagging rather than a functional problem — relative
imports work correctly here since `cli.py` is always invoked as part of the
`salasblog2` package — but bringing it in line with `import
salasblog2.generator` / `import salasblog2.raindrop` style used elsewhere
would remove the one exception to the rule.

## Observations for future improvement

- **`cmd_help`'s option list is hand-synced with the subparsers above it**
  and will silently go stale if a flag is added to one but not the other;
  generating it from argparse's own subparser objects (or just relying on
  `--help`) would remove the duplication.
- **The relative imports** noted above are a straightforward one-line fix
  to bring this file into line with the rest of the codebase's absolute-
  import convention.
