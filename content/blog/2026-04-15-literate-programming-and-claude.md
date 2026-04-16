---
date: '2026-04-15'
tags:
- programming
- ai
title: Literate Programming and Claude
type: blog
---

![](/static/images/uploads/2026-04-15-Screenshot_2026-04-15_at_7.06.13_AM.png)There’s an old concept called **Literate Programming**. It never stuck or took off, but it came back to me the other day. [Here is the Wikipedia explanation](https://en.wikipedia.org/wiki/Literate_programming). My summary of this approach is to write a program (source code) as if it were a chapter in a book — primarily text and diagrams, interspersed with bodies of code. Hold that thought. 

My latest use of Claude Code has yielded some impressive stuff. For the first time I am working with neural networks for image processing and object identification. I am using a camera, the [Oak‑D‑Lite](https://shop.luxonis.com/products/oak-d-lite-1), which has a neural‑net processing chip in the camera itself, thereby offloading a lot of the processing from the attached Raspberry Pi 5. Oak‑D‑Lite is accessed with the [DepthAI package](https://docs.luxonis.com/software-v3/depthai/). Amazingly, Claude.ai knows DepthAI and the camera and neural nets a lot better than I do. With extensive instructions from me it has written code that works and uses these APIs in very granular ways. I ask it to document the code and it does a nice job of it.

### Well commented code
![](https://salas.com//static/images/uploads/2026-04-15-Screenshot_2026-04-15_at_7.06.13_AM.png)