# Salas Blog 2

A simple static site generator for personal blogs and websites, built with Python.

## Features

- Markdown content with YAML frontmatter
- Separate content types: blog posts and raindrops
- Jinja2 templating system
- Client-side search functionality
- Responsive design
- Deploy to Fly.io

## Quick Start

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Create content:
   ```bash
   mkdir -p content/blog content/raindrops
   ```

3. Generate site:
   ```bash
   python b.py generate
   ```

4. Preview locally:
   ```bash
   python -m http.server 8000 -d output
   ```

## CLI Commands

- `python b.py` - Show help
- `python b.py generate` - Generate static site
- `python b.py reset` - Delete generated files
- `python b.py deploy` - Deploy to Fly.io

## Content Structure

```
content/
  blog/
    my-first-post.md
  raindrops/
    quick-note.md
```

### Frontmatter Format

```yaml
---
title: "Post Title"
date: "2024-01-15"
type: "blog"  # or "raindrop"
category: "Tech"
---

Your markdown content here...
```

## Project Structure

```
salasblog2/
├── b.py                 # CLI tool
├── content/            # Markdown content
│   ├── blog/          # Blog posts
│   └── raindrops/     # Short notes
├── templates/         # Jinja2 templates
├── static/           # CSS, JS, images
└── output/           # Generated site
```

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development information.

## Deployment

Configure for Fly.io deployment:

1. Create `fly.toml`
2. Run `python b.py deploy`