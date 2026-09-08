# Feature description for feature F39
## F39 — Auto-generate Blog Drafts from Popular Link Posts
**Priority**: Medium
**Date Created:** 2026-04-18
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Change the Propose workflow to also surface popular raindrop (link) posts and auto-generate one-paragraph blog draft posts from them using the Claude API. A qualifying raindrop is one that is older than X months (default 3) and has more than Y human visits (default 5, from stats). For each qualifying raindrop, call the Claude API using the raindrop's title, URL, domain, tags, note (user's own comment), and excerpt — plus optionally fetching the linked page content — to produce a one-paragraph blog post with a link to the source. Generated posts are saved as drafts (frontmatter `draft: true`, `author: "Claude.ai"`) in content/blog/. The generated paragraph must include a markdown hyperlink to the original source URL. The admin panel shows drafts with a "Post" button that removes the draft flag and triggers incremental site regeneration.

## How to Demo
**Setup**: `uv run bg server`, logged in as admin, with raindrops older than 3 months and more than 5 human visits present.

**Steps**:
1. Open `/admin` → Propose tab → Popular Link Posts section.
2. Click "Generate Draft" on a qualifying raindrop.
3. Open the Drafts tab and confirm the generated draft appears with a one-paragraph body linking to the source URL.
4. Click "Post" and confirm the draft flag is removed and the post appears live.

**Expected output**: Qualifying raindrops can be turned into a Claude-generated draft blog post with one click, and published from the Drafts tab.
