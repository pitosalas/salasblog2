# TF20 — Front Page "See All" Links
**Date Created:** 2026-03-01

## TF20.0 — Add "See all" links to home.html
**Status**: done

**Description**: In `templates/home.html`, added Bootstrap `btn btn-outline-secondary btn-sm` links after the recent blog posts section pointing to `/blog/index.html` and after the raindrops section pointing to `/raindrops/index.html`.

## TF20.1 — Write test
**Status**: done

**Description**: `tests/test_home_see_all.py`: renders home page and asserts both "see all" anchor hrefs are present.
