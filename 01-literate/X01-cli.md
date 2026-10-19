---
version: "1.1"
generated: "2026-10-19"
---

# `cli.py` — The Local Command-Line Front Door

## What this module is for

`cli.py` is a thin `argparse` dispatcher behind the `bg` command
(`uv run bg <command>`). It has grown two kinds of command:

- **Everyday commands** that drive the two core objects:
  - `generate` and `reset`, through `SiteGenerator`
  - `server`, which starts uvicorn
  - `deploy`
  - `sync-raindrops`, through `RaindropDownloader`
- **Content-repair commands**: one-off or occasional fixes run against a
  content tree, locally or on production with `--content /data/content`.
  - `legacy-map`, `legacy-rewrite` and `check-links` (F48)
  - `wp-media` (F49)
  - `wp-tags` (F50)
  - `strip-categories` (F51)

Fly.io's container doesn't start through this file; it imports
`salasblog2.server:app` directly. On production the CLI is used over
`fly ssh console` as `/app/.venv/bin/bg ...`.

## Commands as thin wrappers, not logic

Every `cmd_*` function has the same shape. It builds the right object or
inputs from `args`, calls into a library module, and prints the result:

```python
def cmd_generate(args):
    """Generate the static site"""
    generator = SiteGenerator()
    generator.generate_site()
```

That discipline is deliberate. Logic that lived in `cli.py` would only be
reachable from the shell, invisible to the FastAPI routes and the
scheduler, which trigger the same work. Keeping each `cmd_*` thin means the
CLI and the web server are two callers of the same code, never two
implementations of it. It also keeps the logic testable without argparse.

## The content-repair commands share a shape

Each one is built to be safe to point at production content:

- **Dry run by default.** `legacy-rewrite`, `wp-media` and
  `strip-categories` only report what they would change until `--apply` is
  given.
- **`--content` selects the tree.** It defaults to the local `content/`,
  and production uses `/data/content`.
- **Byte-preserving edits.** `wp-media` rewrites only matched URLs in post
  bodies. `strip-categories` removes only the `category:` line, reading and
  writing raw bytes so line endings survive.

```python
def cmd_strip_categories(args):
    for content_dir in content_dirs(Path(args.content)):
        for md_file in sorted(content_dir.glob("*.md")):
            text = md_file.read_bytes().decode("utf-8")
            new_text = remove_frontmatter_key(text, "category")
            ...
            if args.apply:
                md_file.write_bytes(new_text.encode("utf-8"))
```

The `read_bytes()`/`write_bytes()` pair is a fix, not a style choice. The
first version used `read_text()`/`write_text()`. Their newline translation
turned three CRLF files into LF on production, and the change surfaced
only in the GitHub sync diff.

`wp-media` has two separate modes:

- `--extract TAR` copies the WordPress media export into
  `static/images/wp/` and touches no posts.
- Without it, the command rewrites links. It refuses to point a link at a
  file that isn't present.

That split is what allowed the images to be committed and deployed
*before* any post was changed.

## `cmd_server`: two ways to start uvicorn

`cmd_server` is the one everyday command with a real branch.
`reload=True` needs an *importable module string* rather than an app
object, because uvicorn re-imports the module on every file change:

```python
if args.reload:
    uvicorn.run("salasblog2.server:app", host="0.0.0.0", port=args.port, reload=True)
else:
    from salasblog2.server import app
    uvicorn.run(app, host="0.0.0.0", port=args.port)
```

The deferred import in the `else` branch also keeps `import cli` from
pulling in the whole server module unless `server` is run.

## `main()`: argparse subcommands, `func` dispatch

`main()` builds one subparser per command and attaches its handler with
`set_defaults(func=cmd_x)`, so dispatch is a single `args.func(args)`.
`add_help=False` on the top-level parser lets the module print its own
`cmd_help` both for `help` and for no command at all.

## Observations for future improvement

- **`cmd_help` is hand-maintained** and drifts from the subparsers. Its
  `Options:` block, for example, covers only the everyday commands.
  Generating help from argparse, or relying on `--help`, would remove the
  duplication.
- **The repair commands are piling up in one file.** Six of the twelve
  subcommands are content-repair commands, mostly one-off migrations. Once F55 lands, `wp-tags --promote` and
  possibly `strip-categories` are candidates for removal, so the CLI
  reflects what's still useful.
- **`cmd_strip_categories` is the one command with a loop in it.** Moving
  that walk into a library function, as `rewrite_media_content` does for
  `wp-media`, would restore the thin-wrapper rule and make it unit-testable
  without `argparse.Namespace`.
