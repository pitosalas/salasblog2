---
date: '2021-04-06T13:40:22.794000+00:00'
excerpt: 'Say I''ve got: get ''/'' do $random = Random.rand() response.body = $random
  end If I have thousands of requests per second coming to /, will the $random be
  shared and ''leak'' outside the context or...'
tags:
- sinatra
- tips
- ruby
- stackoverflow
- state
- variables
- global
title: ruby - Is a global variable defined inside a Sinatra route shared between requests?
  - Stack Overflow
type: drop
url: https://stackoverflow.com/questions/14388263/is-a-global-variable-defined-inside-a-sinatra-route-shared-between-requests
---

# ruby - Is a global variable defined inside a Sinatra route shared between requests? - Stack Overflow

**URL:** https://stackoverflow.com/questions/14388263/is-a-global-variable-defined-inside-a-sinatra-route-shared-between-requests

**Excerpt:** Say I've got: get '/' do $random = Random.rand() response.body = $random end If I have thousands of requests per second coming to /, will the $random be shared and 'leak' outside the context or...
