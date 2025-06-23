# Salas Blog 2

A simple static site generator for personal blogs and websites, built with Python.

## Features

- **Markdown Processing**: YAML frontmatter + Markdown content
- **Multiple Content Types**: Blog posts, link blog (bookmarks), and custom pages
- **Dynamic Navigation**: Automatic menu generation from pages
- **Template System**: Jinja2 templates with responsive design
- **Search**: Client-side search with JSON index
- **Static Output**: Complete static HTML site generation
- **CLI Tool**: Simple command-line interface (bg.py)
- **Fly.io Ready**: Built-in deployment support
- **Raindrop.io Integration**: Automatic bookmark downloading and synchronization

## Quick Start

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Content directories are already set up:
   ```
   content/blog/      # Blog posts
   content/raindrops/ # Link blog (bookmarks)
   content/pages/     # Custom pages (auto-generate menu items)
   ```

3. Generate site:
   ```bash
   salasblog2 generate
   ```

4. Preview locally:
   ```bash
   python -m http.server 8000 -d output
   ```
   Visit `http://localhost:8000`

## CLI Commands

```bash
salasblog2 <command> [options]
```

### Available Commands
- `salasblog2 generate` - Generate static site
- `salasblog2 reset` - Delete generated files
- `salasblog2 deploy` - Deploy to Fly.io
- `salasblog2 themes` - List available themes
- `salasblog2 sync-raindrops` - Download new bookmarks from Raindrop.io (for link blog)
- `salasblog2 help` - Show help message

### Options
- `--theme THEME` - Use specific theme (for generate command)
- `--reset` - Reset link blog cache (for sync-raindrops command)
- `--count N` - Limit link blog download (for sync-raindrops command)

## Content Structure

```
content/
  blog/                    # Blog posts
    my-first-post.md
  raindrops/              # Link blog (bookmarks)  
    quick-note.md
  pages/                  # Custom pages (auto-generate menu items)
    about.md
    contact.md
```

### Frontmatter Format

```yaml
---
title: "Post Title"
date: "2024-01-15"        # YYYY-MM-DD format
type: "blog"              # blog, drop (link blog), or page
category: "Tech"
---

Your markdown content here...
```

### Generated Site Structure

```
output/
├── index.html            # Home page
├── about.html            # Pages from content/pages/
├── contact.html
├── search.json           # Search index
├── blog/
│   ├── index.html        # Blog listing
│   └── my-first-post.html
├── raindrops/
│   ├── index.html        # Link blog listing  
│   └── quick-note.html
└── static/               # CSS, JS, assets
```

## Project Structure

```
salasblog2/
├── src/
│   └── salasblog2/        # Main Python package
│       ├── __init__.py
│       ├── cli.py         # Unified CLI interface
│       ├── generator.py   # Site generation logic
│       ├── raindrop.py    # Raindrop.io integration
│       └── utils.py       # Utility functions
├── tests/                 # Test suite
│   ├── __init__.py
│   └── test_utils.py
├── content/              # Markdown content
│   ├── blog/            # Blog posts
│   ├── raindrops/       # Short notes  
│   └── pages/           # Custom pages
├── themes/              # Theme system
│   ├── winer/          # Winer theme
│   │   ├── templates/  # HTML templates
│   │   └── static/     # CSS, JS, assets
│   └── salas/          # Salas theme
│       ├── templates/
│       └── static/
├── output/              # Generated site (excluded from git)
├── pyproject.toml       # Package configuration
├── README.md
└── CLAUDE.md
```

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development information.

## Deployment

Configure for Fly.io deployment:

1. Create `fly.toml`
2. Run `python bg.py deploy`