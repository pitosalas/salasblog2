# TF23 — Tag Selection for Blog Posts (UI and API)
**Date Created:** 2026-03-01

## TF23.0 — Define tag vocabulary constant
**Status**: done

**Description**: Add a `BLOG_TAGS` list constant in `utils.py` (or a dedicated `tags.py`) containing the allowed tag strings. This is the single source of truth for available tags.

## TF23.1 — Add tag multi-select to admin create-post form
**Status**: done

**Description**: In the admin create-post template, render `BLOG_TAGS` as a group of checkboxes (or `<select multiple>`). Submit selected tags as a form field. The server handler writes them as a YAML `tags` list in the new post's frontmatter.

## TF23.2 — Add tag multi-select to admin edit-post form
**Status**: done

**Description**: In the admin edit-post template, render `BLOG_TAGS` as checkboxes with pre-checked values matching the post's existing `tags` frontmatter. The server handler updates `tags` on save.

## TF23.3 — Accept tags in XML-RPC newPost and editPost
**Status**: done

**Description**: In `blogger_api.py`, parse a `tags` field from incoming `newPost`/`editPost` structs and write it to frontmatter. If the field is absent, default to an empty list.

## TF23.4 — Write tests for tag persistence and display
**Status**: done

**Description**: Add tests verifying: (a) tags round-trip through create/edit forms, (b) `newPost` with tags writes correct frontmatter, (c) generated `blog_post.html` renders tag badges for posts with tags.
