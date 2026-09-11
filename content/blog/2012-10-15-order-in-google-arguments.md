---
category: '1'
date: '2012-10-15'
subtitle: Does Google give a different answer if you reorder the words in the search?
  What? A trivial question...
tags:
- algorithms
title: Order in Google arguments
type: wp
wordpress_id: 292
---

Does Google give a different answer if you reorder the words in the search? What? A trivial question? Have you ever tried to refine a search by reordering the words? Wouldn’t it be useful if you knew for sure that it would or would not make a difference?

Experiment:

ruby rails bureaucrat gem examples
```
rails bureaucrat gem examples ruby
```
These two searches indeed did produce different results! And not just a reordering of the results. There were at least two results in the top 7 which were present in one and not the other.

Q.E.D.