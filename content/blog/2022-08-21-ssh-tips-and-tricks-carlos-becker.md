---
title: "SSH Tips and Tricks | Carlos Becker"
subtitle: "SSH Tips and Tricks | Carlos Becker –Since ..."
category: "1"
tags: ["2242", "1221", "2241", "1913", "2181"]
date: "2022-08-21"
type: "wp"
wordpress_id: 4076
---
[ SSH Tips and Tricks | Carlos Becker]( https://carlosbecker.dev/posts/ssh-tips-and-tricks/) –Since I joined Charm, I’ve been working and learning more about SSH, and I thought I would share a few quick tips and tricks with you.

Forward Yubikey Agent If you use a Yubikey (you should), you can use it in your remotes by having the key in a SSH agent and forwarding it.

To manage the agent, I strongly recommend yubikey-agent.

You can then forward it in your ~/.ssh/config like the following: