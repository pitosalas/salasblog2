---
broken: false
cache:
  status: invalid-origin
collection_id: 17452361
cover: https://world.hey.com/dhh/avatar-fb368b1ee9b185dc2a09b03eabdb61678dd55244
creator_ref:
  _id: 624427
  avatar: ''
  email: ''
  name: pitosalas
date: '2024-06-16T11:12:44.051000+00:00'
domain: world.hey.com
excerpt: When we introduced a default setup for system tests in Rails 5.1 back in
  2016, I had high hopes. In theory, system tests, which drive a headless browser
  through your actual interface, offer greater confidence that the entire machine
  is working as it ought. And because it runs in a black-box fashion, it should be
  more resilient to imple...
important: false
last_update: '2024-06-17T00:17:34.387000+00:00'
media:
- link: https://world.hey.com/dhh/avatar-fb368b1ee9b185dc2a09b03eabdb61678dd55244
  type: image
raindrop_id: 801922167
raindrop_type: article
tags:
- dhh system-tests end-to-end-tests ruby software-engineering unit-test
title: System tests have failed
type: drop
url: https://world.hey.com/dhh/system-tests-have-failed-d90af718
user_id: 624427
---

# System tests have failed

**URL:** https://world.hey.com/dhh/system-tests-have-failed-d90af718
**Type:** article
**Domain:** world.hey.com

**Excerpt:** When we introduced a default setup for system tests in Rails 5.1 back in 2016, I had high hopes. In theory, system tests, which drive a headless browser through your actual interface, offer greater confidence that the entire machine is working as it ought. And because it runs in a black-box fashion, it should be more resilient to imple...

**Notes:**
DHH declares system tests to be a failed experiment in the attached document. This is surprising to me but then not surprising. Surprised because intuitively it seems that system tests should be better for the stated reasons. And politically because it seems that the Ruby world had accepted that unit tests are easy to write but too brittle. And system tests were more real-life and robust. But not surprised because I have always found system tests a pain to write. But I don’t have large scale experience with that so I tended to agree with the world that system tests (aka end-to-end tests) were better. So here comes #DHH to argue that system tests have failed!
