---
title: "[GEEK] Is Log4J not doing what you expect, or not finding its properties?"
subtitle: "Here’s a handy bit of esoterica: To force Log4J to report on it’s initialization sequence do this:"
category: "422"
tags: []
date: "2004-05-10"
type: "wp"
wordpress_id: 2012
---
Here’s a handy bit of esoterica: To force Log4J to report on it’s initialization sequence do this: 

**java -Dlog4j.debug=true**

(And no, I usually don’t use log4j, I use the Java 1.4 built in logging facility, but some of the libraries I like still use log4j.)