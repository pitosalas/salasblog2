# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based static site generator for personal websites and blogs called "salasblog2". It processes Markdown files with frontmatter to generate static HTML sites that can be deployed on Fly.io.

## Development Setup

This project uses `uv` for Python package and environment management:

1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`
2. Create project: `uv init` (if not already done)
3. Install dependencies: `uv sync`
4. Activate environment: `source .venv/bin/activate` or use `uv run` prefix

## Common Commands

### Static Site Generation (CLI)
- `python b.py` - Show help message
- `python b.py generate` - Process markdown files and generate static HTML site
- `python b.py reset` - Delete all generated files
- `python b.py deploy` - Deploy site to Fly.io

### Development
- `uv sync` - Install/update dependencies
- `uv run python b.py generate` - Generate site using uv
- `uv add <package>` - Add new dependency
- `python -m http.server 8000 -d output` - Preview generated site locally

### Testing
- `uv run pytest` - Run tests
- `uv run pytest tests/` - Run tests in tests directory
- `uv run pytest -v` - Run tests with verbose output

### Code Quality
- `uv run flake8` - Lint code
- `uv run black .` - Format code

### Deployment
- `fly deploy` - Deploy to Fly.io
- `fly logs` - View application logs
- `fly status` - Check deployment status

## Architecture Notes

This is a static site generator that processes Markdown files with frontmatter to create a personal website and blog. Key components:

- **Static Site Generator**: Processes markdown files into HTML using Jinja2 templates
- **CLI Tool (b.py)**: Main interface for site generation, deployment, and management  
- **Markdown Processing**: All content stored as markdown files with YAML frontmatter
- **Dynamic Navigation**: Automatically generates menu items from content/pages/ directory
- **Content Types**: 
  - Blog posts (content/blog/) with listing page
  - Raindrops (content/raindrops/) with listing page  
  - Individual pages (content/pages/) with automatic menu generation
- **Search Functionality**: Client-side search with JSON index
- **Frontmatter Schema**: title, date, type, category fields for each content file
- **Responsive Design**: Mobile-friendly CSS with hamburger menu
- **Static Output**: Generates complete static HTML site for deployment

## Fly.io Deployment

The application is configured for deployment on Fly.io. Key files for deployment:
- `fly.toml` - Fly.io configuration file
- `Dockerfile` - Container configuration
- `requirements.txt` - Python dependencies

## Content Structure

```
content/
  blog/           # Blog posts (.md files)
  raindrops/      # Short notes/raindrops (.md files)  
  pages/          # Individual pages (.md files) - auto-generate menu items
```

## Generated Output Structure

```
output/
  index.html      # Home page
  about.html      # Individual pages from content/pages/
  contact.html    # (automatically added to navigation)
  search.json     # Search index
  blog/
    index.html    # Blog listing page
    post1.html    # Individual blog posts
  raindrops/
    index.html    # Raindrops listing page  
    note1.html    # Individual raindrops
  static/         # CSS, JS, assets (copied from source)
```

## Development Guidelines

- Use uv for dependency management
- Follow PEP 8 style guidelines
- Write tests for new functionality
- All content stored as markdown files with frontmatter
- Use Jinja2 templates for consistent HTML generation
- Keep generated files separate from source content
- Generated output goes to `output/` directory

## Initial Specification
- a simple home page with a simple menu along the top
- blog post pages have a menu
- raindrop post pages have a menu
- there will be a search function
- the content is all in markdown format
- each markdown file is preceded by front matter
- front matter variables are title, date, type, category
- there will be a simple cli with some commands
- the cli will be called b.py
- b.py generate will process all the markdown, use the templates to generate a complete static html web site
- b.py reset will delete all the generated HTML files
- b.py by itself will print a very very short help message
- b.py deploy will deploy the site to fly.io

## Dependencies

Key Python packages used:
- `jinja2` - Template engine
- `markdown` - Markdown to HTML conversion
- `python-frontmatter` - YAML frontmatter parsing

## Current Status

✅ **Complete Static Site Generator**
✅ CLI tool (b.py) with generate/reset/deploy commands
✅ Markdown processing with frontmatter parsing
✅ Jinja2 template rendering system
✅ Dynamic navigation from content/pages/
✅ Blog posts and raindrops with listing pages
✅ Individual pages with automatic menu generation
✅ Responsive CSS with mobile navigation
✅ Client-side search functionality
✅ Search index generation (JSON)
✅ Static file copying and site generation