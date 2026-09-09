# Tag Hints

_Editable reference for the F46 automated tag-cleanup pipeline
(`04-tasks/notdone/TF46-automated-tag-cleanup.md`). Add or revise anything
here — entities, people, projects, name variants, exclusions — and it feeds
into the next batch's tag decisions. Not consumed by any script; read
directly by whoever (or whichever agent) decides tags for a batch._

## Recurring entities to recognize

- **BlogBridge** — Pito's own RSS reader product. Tag `blogbridge`. Appears
  under many spellings/contexts (BlogBridge beta, BlogBridge update, etc.) —
  all the same entity.
- **JavaOne** — the Java conference. Tag `javaone`, distinct from `java`
  (the language itself).

## Naming conventions

- Prefer specific over generic when a tag could collide with an ordinary
  word (e.g. `demo2004` not `demo`, since "demo" the tech conference and
  "demo" the common word would otherwise conflate).
- Lowercase, single word or short hyphenated phrase.

## Established entity tags (keep spelling consistent)

Batch 5 ran as 5 parallel tagging passes and two different passes picked
different spellings for the same entity (`geekdinner` vs `geek-dinner`,
`chavez` vs `hugo-chavez`) — caught and normalized before applying, but
better to avoid it next time. When any of these entities comes up again,
use the exact form below rather than re-deriving one:

- `geek-dinner` (Pito's recurring Boston tech meetup)
- `hugo-chavez` (not bare `chavez`)
- `attention-xml` (not `attentionxml`)
- `eroom` (not `lotus` — company Pito co-founded)
- `demo2004`, `demo2005`, `demo2006`, `demo2008` (the DEMO conference,
  year-specific — not bare `demo`)
- `sun-microsystems` or a specific product (`mysql`, `java`) — not bare `sun`

## People, places, projects (add here)

brandeis
arlington
boston
wikipedia
ros2
robot
mathematics
algorithms
computer-science
chat-gpt
claude-code
codex
llm
law
legal
vscode
software-engineering
apple
macos
ipad
ios
iphone
linux
unix
ruby
ruby-on-rails


## Exclusions

- **Family members** — never tag with a family member's name, even when a
  post mentions or links to one (e.g. a child's blog). Use `personal`
  instead. (Established during batch 5, chunk 2, of the TF46.6 sweep.)
