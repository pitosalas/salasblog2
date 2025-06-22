# Salas Blog 2

A simple static site generator for personal blogs and websites, built with Python.

## Features

- **Markdown Processing**: YAML frontmatter + Markdown content
- **Multiple Content Types**: Blog posts, raindrops (short notes), and custom pages
- **Dynamic Navigation**: Automatic menu generation from pages
- **Template System**: Jinja2 templates with responsive design
- **Search**: Client-side search with JSON index
- **Static Output**: Complete static HTML site generation
- **CLI Tool**: Simple command-line interface (bg.py)
- **Fly.io Ready**: Built-in deployment support

## Quick Start

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Content directories are already set up:
   ```
   content/blog/      # Blog posts
   content/raindrops/ # Short notes
   content/pages/     # Custom pages (auto-generate menu items)
   ```

3. Generate site:
   ```bash
   python bg.py generate
   ```

4. Preview locally:
   ```bash
   uv run python -m http.server 8000 -d output
   ```
   Visit `http://localhost:8000`

## CLI Commands

- `python bg.py` - Show help
- `python bg.py generate` - Generate static site
- `python bg.py reset` - Delete generated files
- `python bg.py deploy` - Deploy to Fly.io

## Content Structure

```
content/
  blog/                    # Blog posts
    my-first-post.md
  raindrops/              # Short notes/thoughts  
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
type: "blog"              # blog, raindrop, or page
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
│   ├── index.html        # Raindrops listing  
│   └── quick-note.html
└── static/               # CSS, JS, assets
```

## Project Structure

```
salasblog2/
├── bg.py                # CLI tool
├── content/            # Markdown content
│   ├── blog/          # Blog posts
│   ├── raindrops/     # Short notes  
│   └── pages/         # Custom pages
├── templates/         # Jinja2 templates
│   ├── base.html      # Base layout with navigation
│   ├── home.html      # Home page
│   ├── blog_post.html # Individual blog post
│   ├── raindrop_post.html # Individual raindrop
│   ├── blog_list.html # Blog listing page
│   ├── raindrops_list.html # Raindrops listing
│   └── page.html      # Individual pages
├── static/           # CSS, JS, assets
│   ├── css/style.css # Main stylesheet
│   └── js/script.js  # Search & mobile menu
├── output/           # Generated site (excluded from git)
└── pyproject.toml    # UV dependencies
```

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development information.

## Deployment

Configure for Fly.io deployment:

1. Create `fly.toml`
2. Run `python bg.py deploy`