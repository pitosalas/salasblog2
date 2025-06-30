---
title: "Rules of Thumb for Software Engineers"
subtitle: "Based on my own experience, some of my favorite books and blog posts, and advice from friends, I’ve ..."
category: "1"
tags: ["1003", "1779", "1886"]
date: "2014-04-12"
type: "wp"
wordpress_id: 106
---
Based on my own experience, some of my favorite books and blog posts, and advice from friends, I’ve come up with this. What do you think? What should I add? Please comment!

#### Personal Effectiveness Rules of Thumb

- 
**When you have your best idea ever, *always* remember that the idea is just 1% of the journey** Yes, ideas are cheap. At least in the world of software engineering and product development, everyone and their grandfather have ideas that may be great. The distance between the idea and the reality is great. [Here’s Steve Jobs about ideas](http://www.kaspertidemann.com/steve-jobs-on-the-difference-between-a-great-idea-and-a-great-product/)

- 
**When your project is late, *never* ADD people** Most of the time this will slow you down. The reason is that with each additional person you add to a project you’ve created that many more paths of communication. If a project is late, adding people to it will make it later. See * [The Mythical Man Month](http://www.amazon.com/The-Mythical-Man-Month-Engineering-Anniversary/dp/0201835959) by Fred Brooks.

- 
**When planning your time, *always* allocate at least 20% to learning more** Software engineering, programming languages, libraries, platforms, hardware and software are constantly changing. It take a real sustained effort to keep yourself up to date. What was a good or best practice a year ago may no longer be right.

- 
**When arguing about a design or a feature, *always* stop and go ask a user.** Good products don’t come from debate around a table, they come from discussion with the actual users. Don’t guess, don’t argue, go ask! This is known as “getting out of the building”.

- 
**When planning a project, *always* work in short increments.** Follow Agile practices, whatever your favorite flavor is, scrum, XP, Kanban, it doesn’t matter. Different teams and people like different approaches. And they change and evolve all the time. But there are eternal truths there. Work in small chunks. Even smaller. Even smaller. Don’t change many things at once because when your code invariably breaks, you won’t be able to tell why.

- 
**When you are spinning your wheels, *always* stop, think, and only then act.** Google It! The amount of knowledge and down and dirty solutions that you can find on google is infinite. See a strange error message? Google it! And learn how to edit the error message, removing the parts that are specific to you so that you get matches. Or ask on the right forum or mailing list. You need to learn how to ask a question in a way that it will be answered. Make it as easy as possible on the answerer. 

- 
**When you are posting on a technical forum, *always* formulate the question carefully.** Here are the best practices:

Explain precisely what you are trying to accomplish
- Give a step by step explanation of what you’ve tried and the result.
- Give code samples, links to github accounts, and so on. If the code samples are not brief, create a [gist](https://gist.github.com) and put the link in the post.
- Include listings of the relevant data, file names, console logs, and versions of various software you use.

- 
**When you are writing a ‘business’ email, *always* follow best-practices**

If you expect action, have a single person in the to:
- Know the difference between reply and reply all. Usually don’t reply all
- The first sentence should state what action you are looking for
- Keep it short and sweet. Make it “skimmable”. 
- Know your audience and write appropriately. 
- Get to the point. Be polite. 

- 
**When you have to write up a design or a spec, *always* keep it to a few pages.** Prefer writing short ‘stories’ over writing long ‘specifications. There is no requirements ‘phase’ to a project any more. Write many short stories and prioritize them relentlessly. If the story is more effort to write than the code, you should be writing the code!.

#### Programming Rules of Thumb

- 
**When coding, *never* go beyond the immediate requirement.** Write only the code you need to solve the problem RIGHT now. You might think that this class clearly will need all this methods even though no one is calling them yet. This almost never works out. Don’t spend time to set things up for what you’ll need in a month. You’re usually wrong.

- 
**When coding, *always* wait to optimize until later.** Optimizing too early is one of the cardinal sins of programming. You never know where the bottleneck will be, The thing you think will be slow, will be fast, and vice-versa. Actually you might end up ripping it out anyway!

- 
**When your own code mystifies or surprises you *never* accept that. Dig deeper.**

**Catch yourself engaging in magical thinking.** If it worked yesterday, and not today, then *something changed.* Similar story as “It worked on my machine, why doestn’t it work in production?” Both of these are a symptom of magical engineering thinking. It’s just a computer. If the behavior changed, then something cause that change in the behavior. Methodically go through each thing that might be different and, like a scientist (or Sherlock) figure out what it was.
- **Don’t be satisfied with blind luck** Copying some code without knowing what is going on is not a good idea. Eventually it will come back to haunt you. Be really curious!. If a certain change fixed the problem, investigate until you understand how it fixed the problem.
- **Learn to Debug** Debugging is a craft in itself. Approach it like a scientist. Don’t poke blindly at the code, or solve the problem just by thinking about it. Have hypotheses to test. Do experiments.

- 
**When your program blows up *always* stop and read the error messages.** Catch yourself jumpint to conclusions or seeing what’s not there. Fight the impulse that you know what must have failed. Often the right answer is right there in the error message. It might be buried in the middle of a lot of noisy trace output, but discipline yourself to actually read it.

- 
**If you think you spot a code smell *always* come back and eradicate it** Train yourself to recognize (and HATE) code smells. Like nails on a blackboard, badly designed code should make your stomach turn or your skin crawl.

 Cut and Paste code. DRY is a law. If you see any duplicated code it is almost always a bad thing. Look for it and kill it.
- This is a fundamental coding skill. When you see non-dry code or other violations, refactor ruthlessly.
- *never* leave dead code behind** Delete it.
- *always* keep your files, methods and functions short** Depending on the language and the program, the right number may vary. But a method that has more than 20 lines is almost always a serious code smell. A guideline would be 10 lines.

- 
**When programming *always* use a source control system.** It’s your safety net. This is especially true when working with other programmers. Learn your SCS tool so you are never reluctant to use it.

- 
**When designing software, *always* keep concerns as separate as possible.** Design for loose coupling. Pay attention to the Single Responsibility principle. Whether it’s a single class or function, a subsystem or module, or a whole system, minimize dependencies. Learn about dependency injection and other techniques for decoupling.

- 
**When doing object oriented programming *always* avoid using class inheritence** While tempting, it is almost always better to avoid using inheritence in your class design. It brings undesireable coupling with little benefit that could be had in a simpler way.

- 
**When programming *always* use ‘intention revealing names’** Chosing the right names for classes, variables, methods is one of the best ways to ‘document’ your code. Follow your language’s naming conventions closely and then create names that reveal your intention. Name things after what they do, not after how they work! Also make sure names are internally consistent. (Ref: [Intention Revealing Names](http://c2.com/cgi/wiki?IntentionRevealingNames))

- 
**When programming, *always* comment your code, but not too much.** The exact line is a matter of (fervent) debate but it is almost universally accepted that having no comments is a bad idea and that its easy to have too many comments. Keep your comments at the start of each source file, and at the start of each method. Occasionally you might want to put a few lines of comments inline. But that desire often alerts you to a refactoring opportunity.

- 
**When learning new things *never* fall in love with the shiny toys** It’s ok to be proud in your expertise and trying to perfect your craft. But platforms and languages come and go, and you must remain alert to newer and better ways to solve problems as they are invented. Don’t fall in love with a language or platform. It will change and the specific details you memorized will eventually become useless.

#### Credits
Many of these are from books, blogs and my own experience. I will list all the credits that I can identify but I think in some cases these rules are so deeply embedded that I cannot recall where I got them from. If you see sonething that you think you came up with, I appologize!

- [Practices of a Professional Developer](http://www.khebbie.dk/gist/9719703) by Klaus Hebsgaard
- [Practical Object Oriented Design in Ruby](http://www.poodr.com) by Sandy Metz
- [The Mythical Man Month](http://www.amazon.com/The-Mythical-Man-Month-Engineering-Anniversary/dp/0201835959) by Fred Brooks
- [The Pragmatic Programmer](http://www.amazon.com/The-Pragmatic-Programmer-Journeyman-Master/dp/020161622X) by David Thomas
- [Debugging: The Science of Deduction](https://speakerdeck.com/daniellesucher/debugging-the-science-of-deduction)