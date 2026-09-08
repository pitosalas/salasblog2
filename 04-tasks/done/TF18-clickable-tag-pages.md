# TF18 — Clickable Tag Pages
**Date Created:** 2026-03-01

## TF18.0 — Read tags from blog post frontmatter
**Status**: done

**Description**: In `generator.py` `load_posts()`, added `'tags': parsed['metadata'].get('tags', [])` to the base `post_data` dict for all content types.

## TF18.1 — Add generate_tag_pages() to SiteGenerator
**Status**: done

**Description**: Added `generate_tag_pages(posts)` to `SiteGenerator`. Groups posts by slugified tag, renders `tag_page.html` to `output/tags/<slug>/index.html`. Called from `generate_site()` after listing pages.

## TF18.2 — Create tag_page.html template
**Status**: done

**Description**: New template `templates/tag_page.html` extending `base.html`. Shows tag name as heading with post count, lists all posts with title, date, category badge, and excerpt.

## TF18.3 — Link tags on blog_post.html
**Status**: done

**Description**: Added `{% for tag in post.tags %}` badge loop with `slugify` filter linking to `/tags/<slug>/index.html`.

## TF18.4 — Link tags on blog_list.html
**Status**: done

**Description**: Added tag badge loop below the category badge in each post's metadata row.

## TF18.5 — Link tags on home.html
**Status**: done

**Description**: Added tag badge loop below the category badge in each recent post card.

## TF18.6 — Slugify tag names for URLs
**Status**: done

**Description**: Added `slugify_tag(tag)` to `utils.py`: lowercase, strip non-word chars, collapse spaces/underscores to hyphens, strip leading/trailing hyphens. Registered as `slugify` Jinja2 filter in generator and all test environments.

## TF18.7 — Write tests
**Status**: done

**Description**: `tests/test_tag_pages.py`: 5 slugify unit tests + 3 template rendering tests + 1 file-output test. All 11 pass.

## TF18.8 — Filter numeric tags
**Status**: done

**Description**: Added `{% if not tag.isdigit() %}` condition to tag badge loops in `blog_post.html`, `blog_list.html`, and `home.html` to filter out numeric-only tags (WordPress import artifacts).
