---
version: "1.1"
generated: "2026-09-08"
---

# `blogger_api.py` — MarsEdit Over XML-RPC

## What this module is for

Salasblog2's primary authoring surface is its own web admin panel — but the
project also wants to support **MarsEdit**, a dedicated Mac blogging client
that many writers prefer for offline drafting, image handling, and a proper
text editor. MarsEdit doesn't know anything about this project's REST routes;
it only speaks two aging but still-common XML-RPC dialects: the **Blogger
API** and the **MetaWeblog API**. `blogger_api.py` is the adapter that makes
this Python/FastAPI blog look, from MarsEdit's point of view, like a server
those protocols were designed for.

The module doesn't parse or build XML itself — that job belongs to
`server.py`'s `/xmlrpc` route, which now uses Python's standard-library
`xmlrpc.client` for marshalling (see the `05-server.md` companion doc for
why that mattered). `blogger_api.py` picks up cleanly-typed Python
arguments and does the actual work: write a post, read a post, delete a
post, upload an image — using the same content-directory conventions as the
rest of the site.

## Two protocols, one implementation

Blogger API and MetaWeblog API overlap heavily but differ in two ways: an
`appkey` parameter Blogger requires and MetaWeblog doesn't, and the shape of
the "content" argument (Blogger historically expects a single string;
MetaWeblog expects a `struct` with named fields like `title`,
`description`, `mt_keywords`).

Rather than implement both protocols in full, `BloggerAPI` implements the
Blogger methods as the *real* logic, and gives each MetaWeblog method a
one-line wrapper that just injects a placeholder `appkey` and delegates:

```python
def metaweblog_newPost(
    self, blogid: str, username: str, password: str, struct, publish: bool,
    *, background_tasks=None,
) -> str:
    """MetaWeblog API newPost - maps to blogger_newPost with added appkey"""
    return self.blogger_newPost(
        "metaweblog", blogid, username, password, struct, publish,
        background_tasks=background_tasks,
    )
```

This is the *adapter pattern* in its simplest form: one canonical
implementation, two thin protocol-shaped faces on top of it. The read-only
`metaweblog_get*` methods go a step further and *reshape the response*,
since MetaWeblog's field names differ from Blogger's (`description` vs.
`content`, plus a `categories` array Blogger doesn't return — populated
from each post's real frontmatter `tags`, not a placeholder). Both
`blogger_getPost`/`blogger_getRecentPosts` also include a `link` field —
the post's live permalink — which MarsEdit's Link field reads directly.
This started life as a hardcoded `["General", "Technology"]` stub returned
by `metaweblog_getCategories` regardless of what tags a post actually had
(this blog doesn't use a fixed category taxonomy — see F42 — so those two
values meant nothing); found and fixed during F44's manual MarsEdit
verification, alongside the missing `link` field.

## Content parsing: string or struct, decide at the door

Because a request might arrive from either protocol, `content` can show up
as a bare string (old Blogger style — the whole post crammed into one
field) or a `dict`/struct (MetaWeblog style — separate `title`,
`description`, `mt_keywords`). `_parse_content_or_struct()` is the single
place that decides which shape it got and normalizes both into the same
`(title, body, tags)` triple every caller downstream can rely on:

```python
def _parse_content_or_struct(self, content) -> tuple[str, str, list]:
    if isinstance(content, dict):
        title = content.get("title", "Untitled Post")
        body = content.get("description", content.get("content", ""))
        raw_tags = content.get("mt_keywords", content.get("tags", ""))
        ...
    elif isinstance(content, str):
        title, body = self._parse_content(content)
        return title, body, []
```

`tags` gets the same double-shape treatment: MarsEdit's `mt_keywords` field
can be a comma-separated string *or* an array, depending on client and
transport version. The code checks `isinstance(raw_tags, str)` and only
splits on commas in that case — passing an already-split list straight
through. This kind of defensive type-checking at a protocol boundary is
exactly where it belongs: once `_parse_content_or_struct()` returns, nothing
else in the module needs to think about MarsEdit's quirks again.

For the plain-string Blogger fallback, `_parse_content()` makes a heuristic
guess at where the title ends and the body begins — first checking for an
explicit `<title>...</title>` wrapper, then falling back to "is the first
line short and unpunctuated enough to be a title." It's a guess, not a
parse, and the docstring says so; there's no format here that guarantees a
correct split.

## The write pipeline: local file → volume backup → regenerate

Creating or editing a post is a three-stage pipeline, and the ordering
matters:

```mermaid
sequenceDiagram
    participant M as MarsEdit
    participant B as BloggerAPI
    participant FS as Local content/blog/
    participant V as /data (Fly volume)
    participant G as SiteGenerator

    M->>B: blogger.newPost(title, body, tags, publish)
    B->>B: authenticate or raise Fault(401)
    B->>FS: write post.md (flush + fsync)
    B->>V: copy to volume (skipped locally)
    alt volume backup fails
        B-->>M: Fault(500) — post written but not backed up
    end
    alt publish=true
        B->>G: regenerate (background task if given one)
    end
    B-->>M: return filename
```

**Why fsync?** `_write_post_file()` calls `f.flush()` then
`os.fsync(f.fileno())` before returning. A plain `write()` can leave data
sitting in the OS page cache; if the container were to crash a moment
later, the post could simply not exist on disk despite the write call
having "succeeded." `fsync` forces the write to durable storage before
`blogger_newPost` moves on to the next stage — a small cost paid once per
post, in exchange for not silently losing content a user just typed.

**Why raise on backup failure?** `_backup_to_volume()`'s failure path calls
`self._create_fault(500, ...)`, converting a Python exception into an
XML-RPC `Fault` MarsEdit will actually show the user. This exists because
of a real production incident (documented in this project's feature
history as F34): if a volume write silently fails, the post exists only in
the container's ephemeral local copy, and the next scheduled git sync's
`rsync --delete` step would wipe it out before it ever reached persistent
storage — with nothing to tell the author it happened. Surfacing the
failure loudly, immediately, is the fix; a caught-and-ignored exception
here would have reintroduced the exact bug that shipped once already.

**Why is regeneration backgroundable?** Every publish triggers
`generator.incremental_regenerate_post()`, which rewrites the individual
post page, the blog listing, the home page, and the search index — real
I/O against thousands of existing files. Done synchronously, that's what a
MarsEdit user experiences as "Post button hangs for several seconds."
`_regenerate_and_verify()` accepts an optional FastAPI `background_tasks`;
when the XML-RPC route supplies one, regeneration runs *after* the
response is already on the wire, so MarsEdit gets its "success" reply
immediately and the site catches up a moment later:

```python
def _regenerate_and_verify(self, filename, operation, background_tasks=None):
    if background_tasks is not None:
        background_tasks.add_task(self.do_regenerate_and_verify, filename, operation)
    else:
        self.do_regenerate_and_verify(filename, operation)
```

The trade-off is honest, not hidden: a background regeneration failure can
no longer be reported back to the caller as a fault, because the response
already went out. `do_regenerate_and_verify()` still checks that every
expected output file exists afterward and raises if not — but when running
in the background, that raise only reaches the log, not the user. This is
the same responsiveness-over-strict-confirmation trade this project makes
elsewhere (the web admin form's save button behaves identically).

## Local-only vs. production: one `Path("/data").exists()` check

The Fly.io deployment mounts a persistent volume at `/data`; a laptop
running the server locally has no such thing. Two places in this module —
`_backup_to_volume()` and the image-upload path in
`metaweblog_newMediaObject()` — need to skip their volume-copy step
entirely when that mount doesn't exist, rather than attempting a doomed
write and treating the failure as an error:

```python
if not Path("/data").exists():
    logger.info(f"No /data volume present (local dev) — skipping backup for {file_path}")
    return
```

This mirrors a pattern already used by `generator.py` and `raindrop.py` for
detecting whether `/data/content` is the active content source. The
specific bug this fixed: on macOS, attempting to *create* `/data` (which
doesn't exist there) fails with `EROFS — Read-only file system`, because
the machine's root filesystem is a sealed, read-only system volume. Before
this check existed, every local MarsEdit post failed at the backup step
with exactly that OS error, even though the post itself had already been
written successfully to the local `content/blog/` directory.

## Authentication: two tiers, one deliberately loose

`_authenticate()` checks the supplied username/password against
`BLOG_USERNAME`/`BLOG_PASSWORD` environment variables — and if those don't
match, falls back to accepting *any* non-empty username and password:

```python
fallback_auth = bool(username and password)
```

This is explicitly a development-mode convenience (the log message says as
much), but it applies unconditionally — there's no environment check
distinguishing "running locally" from "running in production." Anyone who
knows the XML-RPC endpoint exists can authenticate with literally any
non-empty credentials. See the closing observations below.

## Error reporting: `Fault` as the one true error channel

Every public method funnels failures through `_create_fault()`, which logs
and raises `xmlrpc.client.Fault(code, message)` — never a bare `Exception`,
never a silent `return None`. This matters because `Fault` is the only
exception type the XML-RPC layer (`server.py`) knows how to translate back
into something MarsEdit's UI can actually display with the right error
code. A generic exception reaching that layer still gets converted to a
`Fault`, but with a hardcoded `500` and no semantic meaning — so
`blogger_getPost()`'s 404-with-a-"did you mean" hint, or
`_authenticate_or_raise()`'s 401, are only useful to the end user because
they're raised as *specific* faults at the point where the specific
context (which post, which credential) is still available.

## Observations for future improvement

- **The open-fallback authentication should be gated on environment**, not
  applied unconditionally. A `PRODUCTION`/`ENVIRONMENT` check (or simply
  requiring `BLOG_USERNAME`/`BLOG_PASSWORD` to be set at all in production)
  would close a real, currently-live gap: any client that knows the
  endpoint exists can authenticate with arbitrary non-empty credentials.
- **`blog_dir` is hardcoded to `content/blog` under the process's working
  directory**, never the volume-first `/data/content/blog` that
  `get_content_directory()` in `server.py` resolves to for the web admin
  path. XML-RPC reads/writes and the web admin's reads/writes can
  therefore be looking at two different directories in production,
  reconciled only by `_backup_to_volume()`'s one-way copy. Routing this
  module through the same volume-aware helper `server.py` already has
  would remove an entire class of "why does MarsEdit see stale content"
  bug. **Confirmed live**, not just theoretical: a user reported MarsEdit
  showing a stale post even after refreshing. A post edited via the web
  admin only ever reaches `/data/content`, invisible to this module's reads
  of `/app/content/blog` until the next scheduled GitHub sync; a container
  restart between a MarsEdit edit and the next MarsEdit read reverts
  `/app/content` to the last-pushed commit via `startup.sh`'s
  `git checkout -f`, while `/data/content` (and the live site) keep the
  newer version. Tracked as a pending chore (`04-tasks/chores.md`), not yet
  fixed.
- **The `try/except Exception: logger.error(...); # Don't raise` pattern
  around regeneration appears three times** (create, edit, delete) with
  identical shape. A small context manager or decorator
  (`@best_effort_regenerate`) would remove the duplication and make the
  "regeneration failure never fails the whole request" policy visible in
  one place instead of three.
- **`_parse_content()`'s title/body heuristic for plain-string Blogger
  payloads is a guess**, not a real parse — a post whose first line happens
  to be a long sentence ending in a period gets no title at all, silently
  falling through to the generic `"Blog Post"` title. Given MetaWeblog's
  structured `struct` form is strictly better and is what MarsEdit actually
  sends in modern use, this fallback path may be closer to dead code than
  load-bearing logic — worth auditing against real traffic before investing
  further in it.
- **Excerpts on listing/home pages are generated independently of this
  module** (`utils.py`'s `create_excerpt_with_info()`), by collapsing a
  post's raw markdown into one line and truncating by character count. Two
  related bugs surfaced during the same MarsEdit verification pass —
  truncation cutting mid-`**bold**`/`[link](url)`/`<tag>`, and collapsing
  newlines before truncating turning a correctly-formatted `## Heading`
  into literal `##` text — both now fixed, but worth noting here since a
  MarsEdit-authored post is exactly what exposed them.
