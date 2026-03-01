# Spec for salasblog2
* Create a web site and blog from a collection of configurations and markdown files

## Overview

Salasblog2 is a personal blogging platform built with Python and FastAPI. It combines a static site generator (using Jinja2 templating and Markdown/YAML frontmatter content files) with a live web server. Content is organized into three types: blog posts, raindrop link blog entries (synced from Raindrop.io bookmarks), and static pages. The site is deployed to Fly.io with persistent volume storage and a GitHub repository as a backup. A web admin interface supports creating, editing, and deleting posts, and a tag system generates per-tag listing pages.

## Key Integrations & Features

The app integrates with Raindrop.io via its REST API to automatically sync bookmarks into a "link blog" section on a configurable schedule. It also implements an XML-RPC Blogger API endpoint for compatibility with desktop blog editors like MarsEdit. Dual content storage (Fly.io persistent volume + GitHub) is maintained via a scheduled Git sync. A visitor classifier distinguishes human users from AI crawlers and search engines, and per-visit timestamps are stored so the admin Stats tab can filter by today/week/month/year. Static file serving is hardened against path traversal, symlink escapes, and hidden file exposure. The CLI (`uv run bg`) provides commands to generate the static site, run the dev server, sync raindrops, and deploy to Fly.io.
