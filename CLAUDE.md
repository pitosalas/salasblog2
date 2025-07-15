# CLAUDE.md

Development guidance for Claude Code when working on this salasblog2 codebase.

## Development Workflow

- Use `uv sync` to install dependencies
- Use `uv run` prefix for commands or activate with `source .venv/bin/activate`
- Test changes with `salasblog2 generate` and `salasblog2 server`
- Focus on the "test" theme when working on themes

## Code Style

- Python function comments: brief, 3 lines max, focus on what/why not parameters
- Parameter names should be meaningful and descriptive
- Avoid single-line functions unless they serve a clear purpose
- Avoid if/else with more than 3 branches - refactor instead
- **Minimize JavaScript usage**
- Keep CSS simple, never inline in HTML
- Use existing CSS files or modify them

## Content Directory Structure

### Key Directories
- **`/data/content/`** - Persistent volume storage (production source of truth)
- **`/app/content/`** - Git repository content (development/local)
- Generator prioritizes `/data/content/` if it exists, falls back to local `content/`

### Content Subdirectories
- **`blog/`** - Blog posts with YAML frontmatter + markdown
- **`raindrops/`** - Link blog posts from Raindrop.io bookmarks  
- **`pages/`** - Static pages (About, Contact, etc.)

### Content File Format
All content files use YAML frontmatter + markdown:
```yaml
---
title: "Post Title"
date: "2024-01-15"
type: "blog" | "drop" | "page"
category: "General"
---
Markdown content here...
```

### Content Lifecycle
- **Creation**: Blog API (MarsEdit) → `/app/content/blog/` → immediate backup to `/data/content/`
- **Raindrops**: API fetch → `/data/content/raindrops/` directly
- **Sync**: Scheduler syncs `/data/content/` ↔ GitHub via `/app/content/`
- **Generation**: Reads from `/data/content/` (or `/app/content/` fallback)

## Testing & Quality

- Run `salasblog2 generate` to test static generation
- Run `salasblog2 server` to test API functionality
- Check themes with `salasblog2 generate --theme test`

## Debugging
- Before writing a test, read the corresponding source files to make sure you understand them
- Tests should succeed if there is no bug and fail if there is a bug
- Tests should not verify that a bug is there

