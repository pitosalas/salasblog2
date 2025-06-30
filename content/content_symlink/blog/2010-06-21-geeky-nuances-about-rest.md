---
title: "[GEEKY] Nuances about REST"
subtitle: "While teaching at Brandeis University this summer (see Cosi JBS Web Site"
category: "538"
tags: []
date: "2010-06-21"
type: "wp"
wordpress_id: 706
---
While teaching at Brandeis University this summer (see [Cosi JBS Web Site](http://iceland.cs.brandeis.edu/webapps/FrontPage?from=navigationbox)) I’ve come to think a lot more deeply about the often cliche’d ‘REST’ approach to developing Web Services APIs.
As everyone always says, when you try and explain something, you discover the little gaps in your own understanding, and end up learning at least as much from your students as they are learning from you, which is cool, but for another day.

The essence of the subtlety is captured in the introductory paragraphs of [“Put or Post: The Rest of the Story”](http://jcalcote.wordpress.com/2008/10/16/put-or-post-the-rest-of-the-story/) (an article that was discovered and shared by one of the students 🙂

> “Web service designers have tried for some time now to correlate CRUD (Create, Retrieve, Update and Delete) semantics with the Representational State Transfer (REST) verbs defined by the HTTP specification–GET, PUT, POST, DELETE, HEAD, etc.

So often, developers will try to correlate these two concepts–CRUD and REST–using a one-to-one mapping of verbs from the two spaces, like this: Create = PUT, Retrieve = GET, Update = POST, Delete = DELETE.

[…snip…]

The crux of the issue comes down to a concept known as **idempotency**. An operation is idempotent if a sequence of two or more of the same operation results in the same resource state as would a single instance of that operation.

According to the HTTP 1.1 specification, GET, HEAD, PUT and DELETE are idempotent, while POST is not.

That is, a sequence of multiple attempts to PUT data to a URL will result in the same resource state as a single attempt to PUT data to that URL, but the same cannot be said of a POST request.” (from [“Put or Post: The Rest of the Story”](http://jcalcote.wordpress.com/2008/10/16/put-or-post-the-rest-of-the-story/) )

**Idempotency**, hello? Viagra anyone?

This is subtle stuff. Suffice it to say that I bet the majority of people who talk about REST, and even implement it, are not aware of the nuance. It ties together what HTTP verb to use with the details of what resource is being touched and for what purpose.

It’s an open question to me whether or how this nuance matters in the real world.

Perhaps cloud caching services (CDNs) or other elements of the cloud make assumptions about the exact semantics of the HTTP verbs. Or perhaps there are enough violations of these principles that as a **practical matter** they are just of **theoretical importance**.

If you are interested, I recommend that article, as well as [several others that I put in the intro to the lecture in the course which covered REST](http://iceland.cs.brandeis.edu/webapps/RestWebServ?from=wikipage).

(In retrospect, REST deserves a complete lecture of its own rather than being part of a much broader and general topic of ‘Web Services and Cloud Computing.” Next time.)