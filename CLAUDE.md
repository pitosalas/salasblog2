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
- `salasblog2` - Show help message
- `salasblog2 generate` - Process markdown files and generate static HTML site (uses "winer" theme by default)
- `salasblog2 generate --theme salas` - Generate site using the original "salas" theme
- `salasblog2 generate --theme winer` - Generate site using the "winer" theme (scripting.com style)
- `salasblog2 themes` - List available themes
- `salasblog2 reset` - Delete all generated files
- `salasblog2 deploy` - Deploy site to Fly.io

### Development
- `uv sync` - Install/update dependencies
- `uv run salasblog2 generate` - Generate site using uv
- `uv add <package>` - Add new dependency
- `python -m http.server 8000 -d output` - Preview generated site locally
- `uvicorn src.salasblog2.server:app --host 0.0.0.0 --port 8000` - Run development server with API

### Server & API
- Server runs on port 8000 by default
- XML-RPC endpoint: `/xmlrpc` (for blog editors like MarsEdit)
- RSD discovery: `/rsd.xml` (for automatic blog API detection)
- Authentication: Set `BLOG_USERNAME` and `BLOG_PASSWORD` environment variables

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

This is a well-structured Python package that provides a static site generator with Raindrop.io integration. Key components:

### Package Structure (src/salasblog2/)
- **cli.py**: Unified command-line interface with argparse subcommands
- **generator.py**: Core SiteGenerator class for processing Markdown and generating HTML
- **server.py**: FastAPI server with XML-RPC Blogger API support for blog editors (MarsEdit, etc.)
- **blogger_api.py**: Blogger API implementation for XML-RPC compatibility
- **raindrop.py**: RaindropDownloader class for API integration
- **utils.py**: Reusable utility functions for date formatting, markdown processing, etc.
- **__init__.py**: Package metadata and version information

### Key Features
- **Static Site Generator**: Processes markdown files into HTML using Jinja2 templates
- **Unified CLI**: Single `salasblog2` command with subcommands for all functionality
- **FastAPI Server**: Development server with XML-RPC Blogger API support
- **Blog Editor Integration**: Compatible with MarsEdit, Windows Live Writer, and other XML-RPC blog editors
- **Markdown Processing**: All content stored as markdown files with YAML frontmatter
- **Dynamic Navigation**: Automatically generates menu items from content/pages/ directory
- **Content Types**: 
  - Blog posts (content/blog/) with listing page
  - Link blog (content/raindrops/) with listing page  
  - Individual pages (content/pages/) with automatic menu generation
- **Search Functionality**: Client-side search with JSON index
- **Frontmatter Schema**: title, date, type, category fields for each content file
- **Theme System**: Modular themes with templates and static assets
- **Raindrop.io Integration**: Automated bookmark downloading and markdown conversion
- **Installable Package**: Proper Python package with entry points

## Fly.io Deployment

The application is configured for deployment on Fly.io. Key files for deployment:
- `fly.toml` - Fly.io configuration file
- `Dockerfile` - Container configuration
- `requirements.txt` - Python dependencies

## Content Structure

```
content/
  blog/           # Blog posts (.md files)
  raindrops/      # Link blog (bookmarks) (.md files)  
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
    index.html    # Link blog listing page  
    note1.html    # Individual link blog posts
  static/         # CSS, JS, assets (copied from source)
```

## Theme System

The site generator supports multiple themes, allowing you to switch between different designs and layouts:

### Available Themes
- **winer**: A clean, minimalist theme inspired by Dave Winer's scripting.com
  - Features: Tab navigation, serif typography (Georgia), simple blog-style layout
  - Header: Artistic gradient background with site title
  - Style: Classic early web/blog aesthetic
- **salas**: The original theme with modern design elements
  - Features: Card-based layout, hamburger mobile menu, modern typography
  - Header: Clean navigation bar with search
  - Style: Contemporary responsive design

### Theme Structure
```
themes/
  winer/
    templates/    # HTML templates for winer theme
    static/       # CSS, JS, and assets for winer theme
  salas/
    templates/    # HTML templates for salas theme  
    static/       # CSS, JS, and assets for salas theme
```

### Creating New Themes
1. Create a new directory under `themes/` with your theme name
2. Add `templates/` and `static/` subdirectories
3. Copy templates from an existing theme as a starting point
4. Customize the templates and styles
5. Use `salasblog2 generate --theme YOUR_THEME_NAME` to test

## Development Guidelines

- Use uv for dependency management
- Follow PEP 8 style guidelines
- Write tests for new functionality
- All content stored as markdown files with frontmatter
- Use Jinja2 templates for consistent HTML generation
- Keep generated files separate from source content
- Generated output goes to `output/` directory
- Each theme should be self-contained in its own directory

## Blog Editor Integration

### Supported Blog Editors
- **MarsEdit** (macOS)
- **Windows Live Writer** (Windows)
- **Other XML-RPC compatible editors**

### Setup Instructions
1. **Run the server**: `uvicorn src.salasblog2.server:app --host 0.0.0.0 --port 8000`
2. **Configure blog editor**:
   - **Blog URL**: `https://your-domain.com/` or `http://localhost:8000/`
   - **XML-RPC URL**: `https://your-domain.com/xmlrpc` or `http://localhost:8000/xmlrpc`
   - **API Type**: Blogger API
   - **Username**: Set via `BLOG_USERNAME` env var (default: `admin`)
   - **Password**: Set via `BLOG_PASSWORD` env var (default: `password`)

### Supported API Methods
- `blogger.getUsersBlogs` - Get blog information
- `blogger.getRecentPosts` - List recent posts
- `blogger.getPost` - Get specific post
- `blogger.newPost` - Create new post (auto-commits to GitHub)
- `blogger.editPost` - Edit existing post (auto-commits to GitHub)
- `blogger.deletePost` - Delete post (auto-commits to GitHub)

## GitHub Integration

### Automatic Git Operations
All blog editor operations (create/edit/delete) automatically commit and push changes to the GitHub repository, ensuring:
- ✅ **Persistent storage** - Posts survive instance restarts
- ✅ **Version control** - Full history of all changes
- ✅ **Single source of truth** - GitHub repo contains all content

### Git Setup Requirements
1. **Deploy key or Personal Access Token** configured in Fly.io secrets
2. **Git credentials** set via environment variables:
   - `GIT_EMAIL` - Email for git commits (default: blog-api@salasblog2.com)
   - `GIT_NAME` - Name for git commits (default: Salasblog2 API)

### Git Setup Commands
```bash
# Set up deploy key (recommended)
ssh-keygen -t ed25519 -C "salasblog2-deploy"
fly secrets set SSH_PRIVATE_KEY="$(cat ~/.ssh/id_ed25519)"

# Or use Personal Access Token
fly secrets set GIT_TOKEN="your_github_token"

# Configure git credentials (optional, has defaults)
fly secrets set GIT_EMAIL="your-email@domain.com"
fly secrets set GIT_NAME="Your Name"
```

### Git Operation Flow
1. **Blog editor creates/edits/deletes post** → File operation on Fly.io instance
2. **Site regeneration** → Only affected pages updated (incremental)
3. **Git commit and push** → Changes automatically pushed to GitHub
4. **Persistence guaranteed** → All content stored in GitHub repository

## Raindrop.io Integration (rd_dl)

The project includes `rd_dl`, a CLI tool for downloading bookmarks from Raindrop.io and integrating them with the static site generator.

### rd_dl Overview
- Fully embedded CLI tool for downloading bookmarks from Raindrop.io using their REST API
- Outputs directly to `content/raindrops/` directory for seamless integration
- Maintains idempotent operation - only downloads new bookmarks
- Generates markdown files with aligned frontmatter format
- Single self-contained file (`rd_dl.py`) with unified dependency management

### rd_dl API Reference
- Documentation: https://developer.raindrop.io
- Authentication: Access token required (set RAINDROP_TOKEN environment variable)
- Main endpoints: Collections, Raindrops, User, Tags, Filters, Import/Export

### rd_dl Usage
- `salasblog2 sync-raindrops` - Download new bookmarks from Raindrop.io (for link blog)
- `salasblog2 sync-raindrops --reset` - Delete all existing link blog posts and rebuild from scratch
- `salasblog2 sync-raindrops --count N` - Limit the number of link blog posts to download

### rd_dl Implementation
- Python CLI tool using uv for dependency management
- Uses requests library for API calls
- Handles authentication with access tokens
- Remembers downloaded items via cache to avoid duplicates
- Formats output as markdown with YAML frontmatter

### rd_dl Specification
- Pulls down all "raindrops" from Raindrop.io
- Idempotent operation - same output when re-run
- Results placed in `content/raindrops/` directory
- Output formatted as markdown files named `YY-MM-DD-counter-title.md`
- Frontmatter includes: title, date, tags, type: "drop", url, excerpt
- Frontmatter format aligned with existing static site generator expectations

## Dependencies

Key Python packages used:
- `jinja2` - Template engine
- `markdown` - Markdown to HTML conversion
- `python-frontmatter` - YAML frontmatter parsing

### Additional Dependencies (for rd_dl integration)
- `requests>=2.31.0` - HTTP requests for Raindrop.io API
- `pyyaml>=6.0` - YAML processing for frontmatter
- `python-dotenv>=1.1.0` - Environment variable management

## Current Status

✅ **Complete Static Site Generator**
✅ CLI tool (salasblog2) with generate/reset/deploy commands
✅ **FastAPI Server with XML-RPC Blogger API**
✅ Blog editor integration (MarsEdit, Windows Live Writer, etc.)
✅ Authentication system for API access
✅ Markdown processing with frontmatter parsing
✅ Jinja2 template rendering system
✅ Dynamic navigation from content/pages/
✅ Blog posts and raindrops with listing pages
✅ Individual pages with automatic menu generation
✅ Responsive CSS with mobile navigation
✅ Client-side search functionality
✅ Search index generation (JSON)
✅ Static file copying and site generation
✅ **Raindrop.io Integration (rd_dl)**
✅ Raindrop.io bookmark downloading with API integration
✅ Frontmatter format alignment between rd_dl and site generator
✅ Direct output to content/raindrops/ directory
✅ Idempotent bookmark synchronization with caching