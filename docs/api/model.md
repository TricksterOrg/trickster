---
title: Model
layout: default
nav_order: 2
parent: API
---


## Model
This section describes entities that live inside Trickster, their properties and purpose.

1. TOC
{:toc}


## Route
Route is the base of Trickster. Each rRoute specify what kind of requests it should match and Responses it should return when it's matched.

### `path` *(required)*
- Path is the url after the hostname the Route should match.
- Path may either be a string or regular expression. If you use regex, you it must match the whole url, otherwise the Route will not be used. Eg. `/endpoint_.` will match `/endpoint_1` or `/endpoint_a` but not `/endpoint_42`. Internally Trickster uses [Python's `re.match`](https://docs.python.org/3/library/re.html).
- If multiple routes match the request, the fist one that was added will be used.

### `method`
- The method which the Route should match.
- Default `GET`.
- Allowed values are `GET`, `HEAD`, `POST`, `PUT`, `DELETE` `CONNECT`, `OPTIONS`, `TRACE` and `PATCH`.

### `id` *(unique)*
- Unique identifier that can be later used to query the Route details.
- Must be a string consisting from letters, numbers and underscore.
- If you don't provide an id, Trickster will generate one.

### `used_count` *(read only)*
- Integer counter of how many times was the Route used to handle a request.

### `authentication`
- If there's an authentication method specified for a Route and the Route matches a request, it will then attempt to authenticate the request. If the authentication fails, it will return `401 Unauthorized` instead of standard response.
- By default there's no authentication.
- Authentication details are explained in further section.

### `responses`
- List of Response objects
- When Route matches request, it will return one the responses based on the configured `response_selection`.
- When Route runs out of available Responses, it will return `404 Not Found` instead.

### `response_selection`
- Algorithm that will be used to select the response that will be returned when the Route matches a request.
- Default `greedy`
- Allowed values:
    - `greedy`: Return the first response in the list of responses that is still valid.
    - `random`: Return random response from all valid responses. You may use `Response.weight` to set the random distribution of Responses.
    - `cycle`: Cycle through all Responses in the order in which they were specified. Skips Responses that are no longer valid.

## Response
Response specifies the data the should be returned from the API as well as other behaviour.

### `id` *(unique within a Route)*
- Unique identifier that can be later used in combination with the Route id to query the Response details.
- Must be a string consisting from letters, numbers and underscore.
- If you don't provide an id, Trickster will generate one.

### `status`
- HTTP status code of the Response.
- Default `200`
- All HTTP statuses (including 700) are supported.

### `weight`
- Weight specifies how often should the Response returned when `random` `response_selection` is used. Response with twice the weight will be returned twice as often.
- Default `0.5`
- Min `0.0`
- Max `1.0`

### `used_count` *(read only)*
- Integer counter of how many times was the Response returned from the API.

### `repeat`
- Number of times the response can be returned from the API before it's deactivated.
- When set to `null`, it will never get deactivated.
- Default: `null`

### `is_active` *(read only)*
- `Boolen`
- The value is `true` until all allowed repeats of Response were exhausted.
- When `is_active` is `false`, the response cannot be returned anymore.

### `delay`
- When delay is specified, Trickster will wait for a random time between the bounds before returning the response.
- Delay is an array of two floats - min and max delay, eg. `[0.5, 1.3]`.
- Default `none`

### `headers`
- Object containing `key:value` pairs of headers that will be returned with response.
- You probably want to at least set the `content-type` header. If you set `body` to be anything but a string and you don't set `headers` at all, Trickster will automatically set them to `{"content-type": "application/json"}`. You can always rewrite the `headers` to anything you want. 
- Default `{}`

### `body` *(required)*
- This is the body of request.
- You can set it to be almost anything and Trickster will return it back to you.
- If you set `body` to be a string, Trickster will return it as is. You should consider to also set a `content-type` header.
- If you set `body` to anything else than a string , Trickster will serialize the body to json. If you also don't specify your own `headers`, it will automatically add `{"content-type": "application/json"}`.

## Complete example

```json
{
    "id": "universal_endpoint",
    "path": "/endpoint_\\w*",
    "method": "GET",
    "auth": {
        "method": "basic",
        "username": "username",
        "password": "password"
    },
    "response_selection": "random",
    "responses": [
        {
            "id": "response_1",
            "status": 200,
            "weight": 0.3,
            "repeat": 3,
            "delay": [0.1, 0.2],
            "headers": {
                "content-type": "application/json"
            },
            "body": {
                "works": true
            }
        },
        {
            "id": "response_2",
            "status": 500,
            "weight": 0.1,
            "repeat": 3,
            "delay": [0.1, 0.2],
            "headers": {
                "content-type": "application/json"
            },
            "body": {
                "works": false
            }
        }
    ]
}
```