---
date: '2024-05-23T22:00:12.278000+00:00'
excerpt: "In a single test file, there\u2019s often overlap among the setup data needed\
  \ for the tests in the file. For whatever reasons, perhaps in an effort to improve\
  \ performance or avoid duplication, test writers often merge the setup code and\
  \ bring it to the top of the file so it\u2019s available to all test cases. [\u2026\
  ]"
tags:
- ruby
- antipattern
- test
title: 'Testing anti-pattern: merged setup data - Code with Jason'
type: drop
url: https://www.codewithjason.com/testing-anti-pattern-merged-setup-data/
---

# Testing anti-pattern: merged setup data - Code with Jason

**URL:** https://www.codewithjason.com/testing-anti-pattern-merged-setup-data/

**Excerpt:** In a single test file, there’s often overlap among the setup data needed for the tests in the file. For whatever reasons, perhaps in an effort to improve performance or avoid duplication, test writers often merge the setup code and bring it to the top of the file so it’s available to all test cases. […]

**Notes:**
Interesting. But I think it goes a little far in calling this an "anti pattern". I mean I see the point, but it's not so terrible that I would label it as anti.

