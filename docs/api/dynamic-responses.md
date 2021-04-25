---
title: Dynamic Response
layout: default
nav_order: 5
parent: API
---

# Dynamic Responses
{: .no_toc }

This section provides details about generating dynamic responses. Dynamic responses allow you to configure a response which will change depending on current state of Trickster, the request and other variables.

> Trickster currently supports variables only in json responses.


1. TOC
{:toc}


## Example

Let's look at an example of dynamic error response:

```json
{
    "body": {
        "called": {"$ref": "$.route.used_count"}
    }
}
```

This response uses one variable - `$.route.used_count`. When you call a Route that uses this Response for the first time, Trickster will return:

```json
{
    "called": 0
}
```

The number `0` will change based on the actual number of times, the Route was used. So next time, the Response will be:

```json
{
    "called": 0
}
```

You can do much more with dynamic responses.


## Context
All variables that can be used are specified within a Response Context. It contains information about the current Route, Response, any errors that occurred etc. You can query these variables using json-path.


### Variables


#### `route`
Variable `route` contains the matched Route. The json for querying is in the same format a contains the same variables as the [Route model](/trickster/api/model.html#route).

For example, you can retrieve the username specified in the authentication like this:
```json
{
    "body": {
        "username": {"$ref": "$.route.auth.username"}
    }
}
```

> Variables `used_count`, `repeat` and `is_active` are updated **after** the Response is generated.


#### `response`
Variable `response` contains the Response object that is going to be returned. The format and variables are the same as the [Response model](/trickster/api/model.html#response).

For example, you can retrieve the the number of times a response was used:
```json
{
    "body": {
        "remaining_uses": {"$ref": "$.response.used_count"}
    }
}
```

> Variables `used_count`, `repeat` and `is_active` are updated **after** the Response is generated.


#### `error`
Variable `error` contains an error object, if an error occurred while generating the response. Commonly, this will happen when a request fails authentication.

Error object contains variables:

- `error`: Short description of the error as string
- `message`: Details explaining the error as string
- `status_code`: HTTP status code of the error as an integer

Example of Error object:

```json
{
    "error": "Unauthorized",
    "message": "Invalid username or password.",
    "status_code": 401
}
```

## Query language
Trickster uses [extended jsonpath language](https://goessner.net/articles/JsonPath/) implemented using the [python `jsonpath-ng` package](https://pypi.org/project/jsonpath-ng/). See the [package homepage](https://github.com/h2non/jsonpath-ng#jsonpath-syntax) for complete syntax.

> This is an experimental feature. The [`jsonpath-ng` library contains some bugs](https://github.com/h2non/jsonpath-ng/issues). Unfortunately it's still the best jsonpath library available. 

### Result list
There's one difference between the `jsonpath` specification and the way Trickster handles lists. Jsonpath always returns a list of query results, even when there's only one result. This means Trickster would always replace a variable with list. For this reason, Trickster checks the number of results a query returned.

- If there's multiple results, Trickster will replace the variable with a list of results.
- If there's only one result, Trickster will replace the variable with that one result.
- If there aren't any results, Trickster will replace the variable with `null`.