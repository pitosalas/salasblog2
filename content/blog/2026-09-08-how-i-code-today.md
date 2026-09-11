---
date: '2026-09-09'
image_size: medium
tags:
- claude
- coding
- software-engineering
title: How I code today
type: blog
---

Over the last three months I have written thousands of lines of code and yet I didn't write any of them, claude.ai wrote them. The world of programming, software engineering, computer science, in my opinion has been turned upside down in a matter of months. 

## How I code today

I've created a process within the world of Claude Code which I use to design, plan and implement code. Many people have created similar ones and so instead of describing mine, in detail, let me explain the general idea. The heart of it is a series of feature specs (in individual numbered markdown files) and for each feature spec a task list (in a different markdown file as well) . It's analogous to a kanban or scrum methodology. When I decide to actually build a feature, I instruct claude code to do it.

## Standards

All this is guided by instructions. The process (described just now) is defined as markdown in a file process.md. The structure and outline of a feature file is guided by a template. Similarly a task list file. There is a code_style.md that has my particular idea of what good code and architcture looks like. All these and more come to bear when I instruct claude code to "implement feature F21 using task list TF21, and just to taskts TF21.1 to TF21.3 and stop there. 

## The Specs and Task Lists

A feature spec starts with a vague directive for example, *create a new feature to add json as an available file format*. Claude using the templates and process elaborates that into a nice spec. For example it may decide that it means we need a new option on the cli. Or it may decide that we should refactor the code first. The spec states the requirements at a high level. Next it will develop that feature spec into a detailed task list with any number of steps. The process has a strict directie not to implement any code until i give it the go ahead.

## The literate doc

One neat part of the process is that I taught claude code how to create "literate programs" from my source code. This is a pretty old idea that creates a document explaining a program by providing explanation interspersed with the actual source code; diagrams when needed, definitions, and so on.

## How well does it work?

It works amazingly well. Yes I have to guide it a lot: what data structures or algorithms or operating system services or packages to use. I have to try and fight its tendency to write 2 to 3 times as many lines of code than are necessary. And I have to review code especially when it is not going well, and claude thinks it's fixed a bug several times over but it keeps not working. 

## Links

* [`j3` - the full package of rules and templates to apply this to your program](https://github.com/Boston-Robot-Hackers/j3)
* [`metawtf` - one of many programs I've written using these tools. Review the feature and task and literate directories to get an impression.](https://github.com/Boston-Robot-Hackers/metawtf)