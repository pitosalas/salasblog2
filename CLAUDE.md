# CLAUDE.md

Development guidance for Claude Code when working on this salasblog2 codebase.

## Development
- Use `uv` for package management and launch commands
- Use `uv run bg` alias for all salasblog2 commands
- Test changes with `uv run bg generate` and `uv run bg server`
- Designed for Fly.io deployment with dual content storage

## Code Style
- Python function comments: brief, 3 lines max, focus on what/why not parameters
- Parameter names should be meaningful and descriptive
- Avoid single-line functions unless they serve a clear purpose
- Avoid if/else with more than 3 branches - refactor instead
- Use as little JavaScript as possible
- Keep CSS simple, never inline in HTML
- Use existing CSS files or modify them
- Code includes .toml files as well as Dockerfile

## Content Architecture
- Generator prioritizes `/data/content/` (production) over local `content/` (development)
- Admin interface requires `SESSION_SECRET` and `ADMIN_PASSWORD` environment variables
- Three content types: blog posts, raindrops (link blog), and pages

## Testing
- It is not necessary to test every possible failure mode and provide fallbacks for bugs in content or code
- Focus on core functionality rather than edge cases

## j2 Framework

This project uses the j2 framework. Run `/refresh` to get oriented, or `/continue` to pick up where you left off.

Coding rules are in `.j2/rules.md`. Project spec is in `.j2/specs/`. Current state is in `.j2/state.md`.
