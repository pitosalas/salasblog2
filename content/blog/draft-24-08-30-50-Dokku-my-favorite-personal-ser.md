---
author: Claude.ai
date: '2026-04-18'
source_raindrop: 24-08-30-50-Dokku-my-favorite-personal-ser.md
source_url: https://hamel.dev/blog/posts/dokku/?utm_source=hackernewsletter&utm_medium=email&utm_term=fav
tags:
- cloud
- deploy
- dokku
- tip
title: 'Dokku: my favorite personal serverless platform – Hamel’s Blog'
type: blog
---

I stumbled across [this post by Hamel Husain on Dokku](https://hamel.dev/blog/posts/dokku/?utm_source=hackernewsletter&utm_medium=email&utm_term=fav) and immediately wanted to spin up a server to try it. The pitch is simple but compelling: it's essentially Heroku, except you own the infrastructure. Hamel runs his entire deployment setup for LLM consulting work on a $7/month VPS, which is a stark contrast to what Heroku charges these days. What caught my attention is how full-featured it is despite the low cost — automatic SSL via Let's Encrypt, basic auth for password-protecting sites, Docker support, git-based deployments, and the ability to scale workers with a single command. The example of deploying private static sites is particularly useful, since GitHub Pages locks that behind an expensive Enterprise plan. I've been looking for something lightweight and self-hosted to replace a patchwork of deployment hacks, and Dokku looks like it might genuinely be that thing.