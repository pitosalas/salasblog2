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
- **Use as little JavaScript as possible**
- Keep css as simple as possible
- Never put css inside html files. Use existing css files or modify existing css files.
- When working on themes, focus on the default "test" theme

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

## Future Refactoring TODO: server.py Code Quality Issues

The server.py file (1433 lines) requires significant refactoring to improve maintainability, security, and performance. Below is a prioritized action plan:

### Phase 1: Critical Security and Architecture Issues
1. **Fix Security Vulnerabilities**
   - Implement hidden file protection (lines 201-272: file serving endpoints expose .env, .htaccess files)
   - Add symlink protection (prevent access to files outside output directory)
   - Sanitize subprocess inputs (lines 608-677, 680-761: git operations vulnerable to injection)
   - Secure admin password storage (line 83: plaintext in global config)

2. **Replace Global State Management**
   - Eliminate global mutable dictionaries (lines 32-44: sync_status, regen_status, config)
   - Implement dependency injection or context managers
   - Fix race conditions in async operations

3. **Split the Monolith** (1433 lines → ~200 lines per module)
   ```
   server_main.py      - FastAPI app setup (~200 lines)
   file_serving.py     - Static file endpoints (~150 lines)  
   admin_routes.py     - Admin and content management (~300 lines)
   api_routes.py       - API endpoints (~200 lines)
   xmlrpc_handler.py   - XML-RPC parsing and routing (~200 lines)
   config_manager.py   - Configuration and validation (~100 lines)
   ```

### Phase 2: High Priority Code Quality Issues
4. **Eliminate Code Duplication**
   - Extract common post/page editing logic (lines 792-819 vs 890-917)
   - Unify new content creation (lines 834-872 vs 932-970)
   - Consolidate file serving endpoints (lines 201-272)
   - Merge preview functions (lines 1006-1089)

5. **Improve Error Handling**
   - Standardize error responses across all endpoints
   - Add comprehensive XML-RPC error handling (lines 1313-1319)
   - Implement proper async error handling (lines 1152-1156)

6. **Simplify Complex Functions**
   - Refactor xmlrpc_endpoint() (97 lines, lines 1232-1329)
   - Break down XML-RPC method routing (11-branch if/elif, lines 1287-1312)
   - Simplify sync logic (lines 1112-1133)

### Phase 3: Medium Priority Improvements
7. **Improve Separation of Concerns**
   - Extract validation logic from setup (lines 46-94)
   - Separate sync logic from UI updates (lines 1090-1161)
   - Split file I/O from business logic (lines 347-385)

8. **Remove Magic Numbers and Hardcoded Values**
   - Replace magic number 10 (line 1112: first sync threshold)
   - Extract hardcoded paths (/data/content/.rd_cache.json, line 1109)
   - Configure timeouts (lines 134, 635, 663)

9. **Fix Async/Threading Issues**
   - Properly handle async tasks (lines 1152-1156)
   - Implement proper async patterns throughout
   - Remove unused ThreadPoolExecutor import (line 19)

### Phase 4: Polish and Performance
10. **Remove Dead Code and Clean Imports**
    - Remove unused mount_static_files() function (lines 275-297)
    - Implement delete_post_endpoint() (lines 966-975: returns 501)
    - Clean unused imports (StaticFiles, HTTPBasic, ThreadPoolExecutor)

11. **Add Performance Optimizations**
    - Implement streaming for large files
    - Add caching for template rendering
    - Limit XML parsing size (prevent DoS, lines 1240-1243)

12. **Improve Documentation and Testing**
    - Add comprehensive docstrings
    - Create unit tests for each extracted module
    - Add integration tests for security fixes

### Success Metrics
- Reduce server.py from 1433 lines to <200 lines
- Eliminate all global mutable state
- Fix security vulnerabilities identified in tests
- Achieve 100% test coverage on extracted modules
- Zero security warnings from static analysis tools