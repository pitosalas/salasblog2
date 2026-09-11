---
category: coding
date: '2026-04-30'
image_size: small
tags:
- Dockerfile
- codex
- robot
title: Using Codex to create a Dockerfile from a running system
type: blog
---

I've been dreading this: My robot's rasberry pi 5 was built months ago. I have been using it a lot, installing, updating and changing code and config. All my code is separately in github repos. But there is a lot more `state` than the github repos. It is in config files, pip installs, and so on. I started to worry about the scenario where the MicroSD on the Pi just bites the dust. This does happen, randomly, and occasionally. 

<img src="/static/images/uploads/2026-04-30-its_a_mad_mad_mad_mad_world_xlg.jpg" alt="alt text" align="left" style="margin-right: 1em;">

* I could make a full and faithful copy of the MicroSD. It's a little time consuming but not hard.
* I could start over with a clean Ubuntu install on a MicroSD and then, from notes and memory, build up to the state I was in before
* I could somehow automate the creation the software, config, and overall state so I could do it over and over again
* I could use this opportunity to build a Dockerfile that does all that. 

All of these were well understood projects, but time consuming. While in theory it sounds like 1-2 hours of work, in my experience it can easily be 1-2 days before you get back to a solid base.  The real pros all use the docker approach. It has the advantage of being relatively easy to instpect and modify and rerun. Given that I was essentially creating a disaster backup, I was not super motivated to embark on any of those. But... something I read this morning gave me this idea.

I turned loose codex on my running system, with instructions that it could read everythng on the disk, but mofify only one directory. My prompt essentially was: inspect everything on this system, files, directories, libraries (like pip install), system installed applications (like sudo apt get). From that build a working, complete dockerfile that when run, recreates that whole environment. 

[Here is what we came up with](https://github.com/Boston-Robot-Hackers/dome-docker). It's not quite working but the approach and technique is fantastic. I did in 2 hours what would have taken me at least a day, maybe more. I know docker pretty well. But I don't know all the places on Ubuntu where "state" is stored. That would have taken a lot of trial and error. More to follow.