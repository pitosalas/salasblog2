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

[... rest of the file remains unchanged ...]