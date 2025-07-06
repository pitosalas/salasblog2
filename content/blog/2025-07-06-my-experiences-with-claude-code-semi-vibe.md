---
category: General
date: '2025-07-06'
title: My experiences with Claude Code - semi vibe
type: blog
---

All the code for this new version of my web site was written by claude code. Yes, I am not exagerating. Here are some of my take aways.

**Amazing** Yes, start with admiting that it is amazing. This is a fairly simple application but it has a fair number of moving parts. The code is all open source so you can see for yourself.

**Process** Basically I have two terminal windows open and vs code on the side. Terminal window 1 is running claude code. What that means is that I `cd` into the app directory and type `claude`. That's it (after installing claude of course. It starts up with kind of a "how can I help you" prompt, kind of like a doctor.

From then on you address it like you would a very fast junior programmer who usually understands what you want and does it. It has full access to your shell, your vscode buffers and your github, in real time. (Again once you have set it up.)
 
**What can you ask it to do** It will code up whole functions and classes. It will create new python, html, css, and any file at all. It is pretty competent at doing that. You can also ask it to suggest designs or compare approaches. Again it's a useful sounding board sometimes, but certainly not an oracle of wisdom.

When I start I have a very specific design and architecture in mind. I will explain how things should work, where the data is, what format it is in and so on. I will give it the url to protocol or format speficiations. I will tell it what python packages to use.

**What it is amazingly good at** Tedious repetitive processes that would be hard to automate. One recent example. I have a directory of about 2000 markdwon files. I had reason to think that some of them had html in them instead of markdown. It checked them all and found 5 that had that and fixed them for me. Or I wanted to rename a particular environment variable but I was not sure where it was being accessed.

**Where it makes me nervous** It is so good that it generates a lot of code. Tell it that you to add logging so that you can monitor better what is happening. It goes crazy and dilligently puts in many more than you would. Ask it to make error reporting more clear and suddenly you have multi-step try/except blocks everywhere. It also is pretty dumb about adding repetitive code. So you really have to keep an eye on it.