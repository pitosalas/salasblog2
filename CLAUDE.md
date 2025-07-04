# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based static site generator for personal websites and blogs called "salasblog2". It processes Markdown files with frontmatter to generate static HTML sites that can be deployed on Fly.io. It also implements the Blogger API to allow client apps like MarsEdit to post content.

## Development Setup

This project uses `uv` for Python package and environment management:

1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`
2. Create project: `uv init` (if not already done)
3. Install dependencies: `uv sync`
4. Activate environment: `source .venv/bin/activate` or use `uv run` prefix

## Code Style and Best Practices

- Python function or method comments should be brief. What it does and any special information. Don't document each parameter
- Make sure the parameter names are useful and meaningful
- Comments on functions and methods should be no more than 3 lines of text
- Any function with just one line is questionable. Make sure it is doing something useful. Analyze and list which functions you think are removable.
- Any if else statement with more than three branches is questionable. Try to write it another way.

## Common Commands

### Static Site Generation (CLI)
- `salasblog2` - Show help message
- `salasblog2 generate` - Process markdown files and generate static HTML site (uses "claude" theme by default)
- `salasblog2 generate --theme salas` - Generate site using the original "salas" theme
- `salasblog2 generate --theme winer` - Generate site using the "winer" theme (scripting.com style)
- `salasblog2 themes` - List available themes
- `salasblog2 reset` - Delete all generated files
- `salasblog2 deploy` - Deploy site to Fly.io
- `salasblog2 server` - Run development server with API

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
- Admin interface: `/admin` (password-protected content management)
- API endpoints: `/api/regenerate`, `/api/sync-status`, `/api/scheduler/status`
- Authentication: Set `BLOG_USERNAME` and `BLOG_PASSWORD` environment variables

### Testing
- `uv run pytest` - Run tests
- `uv run pytest tests/` - Run tests in tests directory
- `uv run pytest -v` - Run tests with verbose output
- `uv run pytest -k "not integration"` - Skip integration tests (require running server)
- `uv run pytest tests/integration/ -v` - Run only integration tests (requires server at localhost:8003)

### Code Quality
- `uv run flake8` - Lint code
- `uv run black .` - Format code

### Deployment
- `fly deploy` - Deploy to Fly.io
- `fly logs` - View application logs
- `fly status` - Check deployment status

## Architecture Notes

This is a well-structured Python package that provides a static site generator with Raindrop.io integration and persistent volume management. Key components:

### Package Structure (src/salasblog2/)
- **cli.py**: Unified command-line interface with argparse subcommands
- **generator.py**: Core SiteGenerator class for processing Markdown and generating HTML
- **server.py**: FastAPI server with XML-RPC Blogger API support and admin interface
- **blogger_api.py**: Blogger API implementation for XML-RPC compatibility
- **raindrop.py**: RaindropDownloader class for API integration
- **scheduler.py**: Git scheduler for automated GitHub synchronization
- **volume_manager.py**: Persistent volume management for Fly.io deployment
- **utils.py**: Reusable utility functions for date formatting, markdown processing, etc.
- **__init__.py**: Package metadata and version information

### Key Features
- **Static Site Generator**: Processes markdown files into HTML using Jinja2 templates
- **Unified CLI**: Single `salasblog2` command with subcommands for all functionality
- **FastAPI Server**: Development server with XML-RPC Blogger API support
- **Admin Interface**: Web-based content management with authentication
- **Blog Editor Integration**: Compatible with MarsEdit, Windows Live Writer, and other XML-RPC blog editors
- **Git Scheduler**: Automated GitHub synchronization with configurable intervals
- **Persistent Volume Management**: Handles volume synchronization for Fly.io deployment
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

The application is configured for deployment on Fly.io with persistent volume support. Key files for deployment:
- `fly.toml` - Fly.io configuration file
- `Dockerfile` - Container configuration
- `requirements.txt` - Python dependencies

### Volume Management
- **Source**: `/app/content` (application content)
- **Destination**: `/data/content` (persistent volume)
- **Synchronization**: Uses rsync with --checksum flag to handle MarsEdit timestamp issues
- **Benefits**: Persistent storage, handles instance restarts, resolves timestamp conflicts

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
- **claude**: The default theme with clean, modern design
  - Features: Responsive layout, clean typography, modern aesthetic
  - Header: Navigation bar with search functionality
  - Style: Contemporary design optimized for readability
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
  claude/
    templates/    # HTML templates for claude theme
    static/       # CSS, JS, and assets for claude theme
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
1. **Run the server**: `salasblog2 server` or `uvicorn src.salasblog2.server:app --host 0.0.0.0 --port 8000`
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

### Git Scheduler
- **Automated sync**: Configurable interval-based GitHub synchronization
- **Conflict resolution**: Handles merge conflicts and sync issues
- **Status monitoring**: API endpoints for scheduler status and health checks
- **Environment variables**:
  - `GIT_SYNC_ENABLED` - Enable/disable automatic git sync (default: true)
  - `GIT_SYNC_INTERVAL` - Sync interval in minutes (default: 5)

## Raindrop.io Integration

The project includes comprehensive Raindrop.io integration for downloading bookmarks and integrating them with the static site generator.

### Raindrop.io Overview
- Fully integrated bookmark downloading from Raindrop.io using their REST API
- Outputs directly to `content/raindrops/` directory for seamless integration
- Maintains idempotent operation - only downloads new bookmarks
- Generates markdown files with aligned frontmatter format
- Comprehensive API coverage with full metadata preservation

### Raindrop.io API Reference
- Documentation: https://developer.raindrop.io
- Authentication: Access token required (set RAINDROP_TOKEN environment variable)
- Main endpoints: Collections, Raindrops, User, Tags, Filters, Import/Export

### Raindrop.io Usage
- `salasblog2 sync-raindrops` - Download new bookmarks from Raindrop.io (for link blog)
- `salasblog2 sync-raindrops --reset` - Delete all existing link blog posts and rebuild from scratch
- `salasblog2 sync-raindrops --count N` - Limit the number of link blog posts to download

### Raindrop.io Implementation
- Python integration using requests library for API calls
- Handles authentication with access tokens
- Remembers downloaded items via cache to avoid duplicates
- Formats output as markdown with YAML frontmatter
- Comprehensive metadata preservation including highlights, tags, and user notes

### Raindrop.io Specification
- Pulls down all "raindrops" from Raindrop.io
- Idempotent operation - same output when re-run
- Results placed in `content/raindrops/` directory
- Output formatted as markdown files named `YY-MM-DD-counter-title.md`
- Frontmatter includes: title, date, tags, type: "drop", url, excerpt
- Frontmatter format aligned with existing static site generator expectations
- Preserves all API metadata: highlights, notes, importance flags, broken link status

## Environment Variables

### Core Configuration
- `BLOG_USERNAME` - Username for admin/API access (default: admin)
- `BLOG_PASSWORD` - Password for admin/API access (default: password)
- `PORT` - Server port (default: 8000)
- `HOST` - Server host (default: 0.0.0.0)

### Git Integration
- `GIT_EMAIL` - Email for git commits (default: blog-api@salasblog2.com)
- `GIT_NAME` - Name for git commits (default: Salasblog2 API)
- `GIT_TOKEN` - Personal access token for GitHub (alternative to SSH key)
- `SSH_PRIVATE_KEY` - SSH private key for GitHub (recommended)
- `GIT_SYNC_ENABLED` - Enable automatic git sync (default: true)
- `GIT_SYNC_INTERVAL` - Sync interval in minutes (default: 5)

### Raindrop.io Integration
- `RAINDROP_TOKEN` - Access token for Raindrop.io API

### Volume Management
- `VOLUME_ENABLED` - Enable volume synchronization (default: true for Fly.io)
- `VOLUME_SOURCE` - Source directory (default: /app/content)
- `VOLUME_DEST` - Destination directory (default: /data/content)

## Dependencies

Key Python packages used:
- `fastapi>=0.104.0` - Web framework for server and API
- `uvicorn[standard]>=0.24.0` - ASGI server
- `jinja2>=3.1.6` - Template engine
- `markdown>=3.8.2` - Markdown to HTML conversion
- `python-frontmatter>=1.1.0` - YAML frontmatter parsing
- `requests>=2.31.0` - HTTP requests for Raindrop.io API
- `pyyaml>=6.0` - YAML processing for frontmatter
- `python-dotenv>=1.1.0` - Environment variable management
- `python-multipart>=0.0.6` - Form data handling
- `itsdangerous>=2.0.0` - Session management
- `schedule>=1.2.0` - Task scheduling for git sync

## Current Status

✅ **Complete Static Site Generator**
✅ CLI tool (salasblog2) with generate/reset/deploy commands
✅ **FastAPI Server with XML-RPC Blogger API**
✅ Blog editor integration (MarsEdit, Windows Live Writer, etc.)
✅ Authentication system for API access
✅ **Admin Interface** with web-based content management
✅ Markdown processing with frontmatter parsing
✅ Jinja2 template rendering system
✅ Dynamic navigation from content/pages/
✅ Blog posts and raindrops with listing pages
✅ Individual pages with automatic menu generation
✅ Responsive CSS with mobile navigation
✅ Client-side search functionality
✅ Search index generation (JSON)
✅ Static file copying and site generation
✅ **Git Scheduler** for automated GitHub synchronization
✅ **Persistent Volume Management** for Fly.io deployment
✅ **Comprehensive Raindrop.io Integration**
✅ Raindrop.io bookmark downloading with API integration
✅ Frontmatter format alignment between Raindrop.io and site generator
✅ Direct output to content/raindrops/ directory
✅ Idempotent bookmark synchronization with caching
✅ **Theme System** with multiple theme support and easy switching

## Web-Based Post Management - TODO

### Phase 1: Extend Existing Blog Post Display
- [ ] Add admin controls to individual blog post pages
  - [ ] Add "Edit" and "Delete" buttons/links on each blog post
  - [ ] Only visible when user is authenticated as admin
  - [ ] Style them subtly (maybe small icons in top-right corner)
- [ ] Add global "New Post" link
  - [ ] Add to header navigation or admin section
  - [ ] Only visible to authenticated admin users
  - [ ] Could be a "+" icon or "New Post" link

### Phase 2: Create Post Editor Interface
- [ ] Create post editing page (`/admin/edit-post/{filename}`)
  - [ ] Load existing post content and frontmatter
  - [ ] Markdown editor with frontmatter form
  - [ ] Save/Cancel actions
- [ ] Create new post page (`/admin/new-post`)
  - [ ] Empty editor with default frontmatter template
  - [ ] Generate filename based on title + current date

### Phase 3: Handle Actions
- [ ] Implement edit/delete endpoints
  - [ ] `POST /admin/save-post` - Save post changes
  - [ ] `POST /admin/delete-post` - Delete post with confirmation
  - [ ] Trigger site regeneration and GitHub sync
- [ ] Add client-side enhancements
  - [ ] Delete confirmation dialog
  - [ ] Auto-save drafts while editing
  - [ ] Success/error notifications

### Benefits of This Approach:
- **Natural workflow** - Edit posts where you read them
- **No duplicate interfaces** - Users see actual blog, not management abstraction  
- **Contextual actions** - Edit/delete actions are right on the content they affect
- **Cleaner admin experience** - No need to navigate to separate management area
- **Familiar pattern** - Similar to WordPress, Ghost, and other CMS admin bars