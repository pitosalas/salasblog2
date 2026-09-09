# I01 Incremental regeneration silently drops content types from search index (and raindrops from home page)

* **Symptom**: after editing a single blog post or raindrop, `search.json` gets
  overwritten with all existing *Pages* removed from search results, until the
  next full site regeneration restores them. Separately, editing a *Page*
  overwrites both `search.json` *and* the home page's "Link Blog" section with
  raindrops removed, until the next full regeneration.

* **What tests have already been done**: found via code review while
  regenerating `01-literate/07-generator.md` (2026-09-09), then confirmed
  directly against `src/salasblog2/generator.py`. Not yet reproduced against a
  running site or covered by a test — this is a static-analysis finding, not
  an observed production incident.

* **Latest theory**: `SiteGenerator.incremental_regenerate_post()`
  (`generator.py:751`) only loads the content type that actually changed, to
  keep incremental edits fast on a ~2800-post blog. To do that, it sets the
  *other* content types to `[]` rather than loading them from disk:

  ```python
  if content_type == "blog":
      blog_posts = changed_posts
      raindrops = self.load_posts("raindrops")
      pages = []
  elif content_type == "raindrops":
      blog_posts = self.load_posts("blog")
      raindrops = changed_posts
      pages = []
  else:  # pages
      blog_posts = self.load_posts("blog")
      raindrops = []
      pages = changed_posts
  ```

  Those same variables then feed both the home page and the search index:

  ```python
  self.generate_home_page(blog_posts, raindrops)
  self.generate_search_index(blog_posts + raindrops + pages)
  ```

  `pages` was never loaded for a `blog`/`raindrops` edit, and `raindrops`
  was never loaded for a `pages` edit — so whichever list is empty gets
  written into both `search.json` (always) and `home.html` (for the
  `raindrops` case specifically) as if that content type no longer exists,
  until the next full `generate_site()` run repopulates it. Nothing else in
  the incremental-regeneration design suggests pages/raindrops should be
  excluded from search or the home page — this looks like an oversight in
  which lists were considered "not needed" for the search/home step, not an
  intentional trade-off.
