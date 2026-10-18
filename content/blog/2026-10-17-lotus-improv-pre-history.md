---
date: '2026-10-17'
tags: []
title: Lotus Improv Pre-History
type: blog
---

In the last few days I've been asked a couple of time about Lotus Improv. I think it was triggered by a wonderful [Improv analysis and retrospective](https://stonetoolsblog.com/lotusimprov-next/) by [Christopher Drum](https://stonetoolsblog.com/author/christopherdrum/) who I never met, but really dug deep in his research. It was great to see such in depth attention to this app from 40 years ago. I mean really, that's research! I was asked on the discussion thread about where the ideas for the Pivot Table came from. Instead of giving a throwaway answer, I sat back and relived those early days...

# How the Pivot Table Came About

Just for the heck of it, I'm going to tell you how the idea came about. It's many years ago, so it's kind of fun to go down memory lane.

## Lotus Was a Spreadsheet Company

Lotus was a spreadsheet company—first, second, and last. That was all that mattered, even though we had lots of other products. 1-2-3 was the massive revenue maker, and if you wanted to get attention within Lotus for a new product, it had to be clearly tied to spreadsheets.

## Looking for Patterns

I was in a research group, and one of the ideas my curiosity led me to was to look at the many books that existed then about good spreadsheet practices. They covered how to run your inventory in 1-2-3, how to run your HR in 1-2-3, how to plan your products with 1-2-3, etc. They had methodologies for structuring spreadsheets, designing formulas, and using the various features of 1-2-3 in those formulas. I got interested in looking for patterns in these structures, so I grabbed a whole bunch of those books and read chapter after chapter about techniques that different people were putting forward.

I noticed a lot of consistent structure. Very commonly, you would have some kind of property along the top row, an entry or item number along the left, and the data values in between—like a normal table, almost like a database. Then they would divide the columns into groups. For example, if the columns were revenue, cost, and profit, they might have four examples of those three columns: one for Q1, one for Q2, one for Q3, and one for Q4. Very standard, very obvious.

## The Semantic Spreadsheet

The funny thing was that the formulas in those columns, even though they were not necessarily adjacent, were essentially the same or very close to being identical. It struck me that it was ridiculous that a person had to come up with those patterns and copy formulas, running the risk of making mistakes—a risk that was very common then and is still very common. As a computer-science person, I thought, "Well, there are algorithms to do that." We could write the formula once—profit equals sales minus cost—and then appropriately tweak it for North America, South America, Q1, whatever. It's still the same formula.

That was part one. I called that the semantic spreadsheet. I still have a paper I wrote way back then.

## Flexible Views

Then I realized the same exact data could be displayed in reverse—e.g., Q1, profit, cost, and revenue for Q1, Q2, Q3, Q4, and so on. The numbers and formulas would be exactly the same; only the display changed. We called those flexible views, which later became known as pivot tables.

## What Was New and What Wasn't

Structuring data like that wasn't a new idea; crosstabs have existed in statistics systems forever. I was aware of that, and in my research I discovered that nobody had come up with the idea of flipping what we call dimensions. Since the underlying data structure I designed for the cells was abstract and had no connection to the display, flipping it wasn't hard.

The main thing I remember from then is Javelin, a character-based product with English-language formulas, but without flexible views or pivot tables. There were also products from Borland with crosstabs. So I would say there were definitely things in Improv that were novel, although there were logical precursors to pivot tables.

It turns out that having the formulas span was actually much more difficult than the pivot-table part, because you had to deal with the fact that formulas were superseded by other formulas, making the ordering of formulas very important—a big headache for the developer.

## Why Improv Failed

Now, talking about the failures of Improv, which I've documented well, the main problem was that it was not a spreadsheet. Even though we tried to call it a spreadsheet, it wasn't. Our import/export, printing, report generation, and database integration could have been better, but we released it before we had all that stuff. The real crux was that users familiar with spreadsheets were confused by the structure, and some common spreadsheet structures could not be represented in Improv without ugly workarounds.

## Landing on the NeXT

Lotus had to protect its big revenue stream from 1-2-3, so we were always in a side corner relative to 1-2-3. That's how we ended up on the NeXT computer—mainly because it removed the competitive issue. There was no 1-2-3, Excel, or Multiplan for it, so there was no cannibalization risk. Steve Jobs was also a very important factor; he became infatuated with Improv and even came up with the name. When he liked it, everyone else seemed to like it as well.

## How It Ended

After that, because Improv didn't do well initially—even though there was a Windows release—pricing jumped all over the place, and it became clear that it was not going to be a good business. That's the story.