# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based personal website and blog called "salasblog2" with additional features beyond basic blogging. It will be deployed on Fly.io. The repository is currently empty and ready for initial development.

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

- **Static Site Generator**: Processes markdown files into HTML using templates
- **CLI Tool (b.py)**: Main interface for site generation, deployment, and management  
- **Markdown Processing**: All content stored as markdown files with YAML frontmatter
- **Template System**: Generates HTML from markdown content using templates
- **Content Types**: Blog posts and "raindrop" posts, both with navigation menus
- **Search Functionality**: Site-wide search capability
- **Frontmatter Schema**: title, date, type, category fields for each content file
- **Static Output**: Generates complete static HTML site for deployment

## Fly.io Deployment

The application is configured for deployment on Fly.io. Key files for deployment:
- `fly.toml` - Fly.io configuration file
- `Dockerfile` - Container configuration
- `requirements.txt` - Python dependencies

## Development Guidelines

- Use uv for dependency management
- Follow PEP 8 style guidelines
- Write tests for new functionality
- All content stored as markdown files with frontmatter
- Use templates for consistent HTML generation
- Keep generated files separate from source content

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
- b.py reset will delete all the genetated markdown
- b.py by itself will print a very very short help message
- b.py deploy will deploy the site to fly.io
- 