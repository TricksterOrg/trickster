---
title: API
layout: default
nav_order: 3
has_children: true
---

# API
Trickster provides an API with some predefined endpoints. Using this API you can specify other Routes Trickster should provide. You can also configure how fast it should respond, set of responses from which it should choose and how to choose, if there should be authentication and much more.


## API from 10 000 feet
This sections attempts to give you top level view on routing in Trickster. Specific [endpoints](/trickster/api/endpoints.html) and [objects](/trickster/api/model.html) are described in their respective sections.

### What are Routes and Responses
The base of Trickster is composed from list of Routes. Route is a specification of an endpoint or set of endpoints that have similiar behaviour. By adding Route, you are adding urls and method which Trickster should react to.

Bellow Routes are Responses. Each Response specifies an http data and metadata Trickster should return, when Route is matched.

> Route can have multiple Responses associated with it. Each Response > has only one Route it belongs to.

### How Routes are resolving
Internally all Routes and Responses are stored in a list in the order they were defined. Order, in which you define them matters.

Assume you just sent a request to Trickster. How does it decide, what it should return back?

#### Find Route
The first step is to find a Route, which matches the request. Tricksters iterates over all the defined Routes and looks for 3 things:

1. Does the of the request match the `path` defined in the Route?
2. Does the http method match the `method` defined in the Route?
3. Does the Route have any valid Responses?

If any of checks fail, move to the next Route. If you run out of Routes, return `404 Not Found`.

#### Authenticate
If all the check pass, Trickster will use that Route. Then it will perform authentication, if it's configured. If you didn't configured authentication, it will skip this step.

If the authentication fail, it will return `401 Unauthorized`. If the authentication succeeds, continue to response selection.

> To reiterate - if the authentication fails, Trickster will not attempt to find another Route.

#### Select Response
In previous steps Trickster found a Route that has some available Responses and we authenticated the request. In this step it will select a proper Response.

Strategy that will be used is controlled by the configured `response_selection`. Here we will assume the Route was configured with `greedy` strategy. That's the default.

This strategy iterates over all Responses in a Route in the order they were added. When it finds a Response that has some uses left, it will return that Response.

> It should never happen that there are no Responses left. When Trickster matches a request to Route, it only looks at Routes that have some usable Responses.

#### Mark Response as used used
After the Response is returned from the API, it's internal counter [`used_count`](/trickster/api/model.html#used_count-1) is increased by 1. (The same applies to the corresponding [`Route.used_count`](/trickster/api/model.html#used_count)). When the `used_count` of a Response reaches the configured [`repeat`](/trickster/api/model.html#repeat) count, the Response will not be considered next time.