# F48 — Repair Legacy Internal Links

**Priority**: Medium

**Date Created:** 2026-10-13

**Done:** yes — verified live 2026-10-13; 21 unfixable dead self-links remain (see TF48.8)

**Tasks File Created:** yes

**Tests Written:** yes

**Test Passing:** yes

**Description**: Many older posts link to other posts on this blog using
URL schemes from earlier blog engines. None of those URLs exist on the
current site, so they 404.

Example: "Why Improv didn't succeed, Part Deux" links to
`/weblogs/archives/000522.html`. The Wayback Machine shows that was
"Why Improv didn't succeed" (Nov 28, 2004), now at
`/blog/2004-11-29-why-improv-didn8217t-succeed.html`.

Legacy self-link schemes found in local content:

* **Movable Type** — `/weblogs/archives/NNNNNN.html`. About 80 links, 43
  distinct IDs, 33 posts.

* **WordPress** — `/YYYY/MM/DD/slug/`. About 60 links.

* **WordPress import leftovers** — `/imported-20111103233638/...` and
  `salascom.wordpress.com/...`. A handful.

Nothing in post frontmatter records the old Movable Type ID, so the mapping
has to be reconstructed.

This feature:

* Builds an old→new URL map as a reviewed data file.

* **The user reviews the map before any post is touched.**

* Rewrites the links in post content, on **production's
  `/data/content/blog` volume** (via `fly ssh`), not only the local repo.

* Adds server redirects (301) for legacy URLs, driven by the same map, so
  inbound links from other sites and search engines also work.

* Adds a checker that reports remaining dead self-links.

**Out of scope**: dead links to *external* sites.

## How to Demo
**Setup**: map built and approved, rewrite applied to production, redirects
deployed.

**Steps**:
1. Open https://salas.com/blog/2004-12-02-why-improv-didn8217t-succeed-part-deux.html
   and click "my earlier posting".
2. Visit https://salas.com/weblogs/archives/000522.html directly.
3. Visit a legacy WordPress URL, e.g. https://salas.com/2008/02/18/about-amzn-and-cloud-computing/.
4. Run the dead-self-link checker.

**Expected output**: step 1 opens "Why Improv didn't succeed". Steps 2 and 3
301-redirect to the matching current posts. Step 4 reports only the
entries the map marks as unmatched.

## Process Gate
After creating this feature file and the corresponding task file, **stop and present the plan to the user**. Do not write any code or content until the user gives explicit approval to proceed.
