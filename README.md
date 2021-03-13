# Trickster
Trickster is a Python/Flask application providing configurable API. It allows you to configure requests and responses using REST API.

## Usecases
- **Local development.** Sometimes your app needs lots of other services to work properly. Setting all that infrastructure might me time consuming and sometimes not even possible. Mock Service allows you to mock all necessary upstream services.
- **Integration testing.** The same way you need to setup infrastructure to develop locally, it might equally difficult to setup integration environment. Some services are just too hard to configure so you can test all scenarios. By using Mock Service you define expected behaviour. If you later find a bug, it's easy to find if your assumptions about the infrastructure was wrong or if there's a bug somewhere else.
- **Performance testing.** When running performance tests, the upstream services might cause a bottleneck. The test then actually tests your infrastructure, not your application. Or you might want to test what your application will do when all the dependencies start responding slowly or raise errors.
- **Distributing work.** Distributing work on new project between teams is challenging when you don't have a working API. Mock Service allows you to specify and document the API beforehand so everyone can start developing as if they have everything they need.


## Basics
Trickster provides an API with some predefined endpoints. Using this API you can specify other Routes Trickster should provide. You can also configure how fast it should respond, set of responses from which it should choose and how to choose, if there should be authentication and much more.

This is the minimal Route:
```python
{
    "path": "/endpoint",
    "responses": [
        {
            "body": "response"
        }
    ]
}
```

As you see, it will match any GET (*default*) request on URL `/endpoint` and will respond with `text`.
To add the route to Trickster, POST it to `/internal/route`:

```sh
curl --location --request POST '/internal/route' --header 'Content-Type: application/json' --data-raw '{
    "path": "/endpoint",
    "responses": [
        {
            "body": "response"
        }
    ]
}'
```

We can then call the newly create endpoint: `curl --location --request GET '/endpoint'`.

## Route
Route is the base of Trickster. Each route specify what kind of requests it should match and Responses it should return when it's matched.

#### `path` *(required)*
- Path is the url after the hostname the Route should match.
- Path may either be a string or regular expression. If you use regex, you it must match the whole url, otherwise the Route will not be used. Eg. `/endpoint_.` will match `/endpoint_1` or `/endpoint_a` but not `/endpoint_42`. Internally Trickster uses [Python's `re.match`](https://docs.python.org/3/library/re.html).
- If multiple routes match the request, the fist one that was added will be used.

#### `method`
- The method which the Route should match.
- Default `GET`.
- Allowed values are `GET`, `HEAD`, `POST`, `PUT`, `DELETE` `CONNECT`, `OPTIONS`, `TRACE` and `PATCH`.

#### `id` *(unique)*
- Unique identifier that can be later used to query the Route details.
- Must be a string consisting from letters, numbers and underscore.
- If you don't provide an id, Trickster will generate one.

#### `used_count` *(read only)*
- Integer counter of how many times was the Route used to handle a request.

#### `authentication`
- If there's an authentication method specified for a Route and the Route matches a request, it will then attempt to authenticate the request. If the authentication fails, it will return `401 Unauthorized` instead of standard response.
- By default there's no authentication.
- Authentication details are explained in further section.

#### `responses`
- List of Response objects
- When Route matches request, it will return one the responses based on the configured `response_selection`.
- When Route runs out of available Responses, it will return `404 Not Found` instead.

#### `response_selection`
- Algorithm that will be used to select the response that will be returned when the Route matches a request.
- Default `greedy`
- Allowed values:
    - `greedy`: Return the first response in the list of responses that is still valid.
    - `random`: Return random response from all valid responses. You may use `Response.weight` to set the random distribution of Responses.
    - `cycle`: Cycle through all Responses in the order in which they were specified. Skips Responses that are no longer valid.

## Response
Response specifies the data the should be returned from the API as well as other behaviour.

#### `id` *(unique within a Route)*
- Unique identifier that can be later used in combination with the Route id to query the Response details.
- Must be a string consisting from letters, numbers and underscore.
- If you don't provide an id, Trickster will generate one.

#### `status`
- HTTP status code of the Response.
- Default `200`
- All HTTP statuses (including 700) are supported.

#### `weight`
- Weight specifies how often should the Response returned when `random` `response_selection` is used. Response with twice the weight will be returned twice as often.
- Default `1.0`
- Min `0.0`
- Max `1.0`

#### `used_count` *(read only)*
- Integer counter of how many times was the Response returned from the API.

#### `repeat`
- Number of times the response can be returned from the API before it's deactivated.
- When set to `null`, it will never get deactivated.
- Default: `null`

#### `is_active` *(read only)*
- `Boolen`
- The value is `true` until all allowed repeats of Response were exhausted.
- When `is_active` is `false`, the response cannot be returned anymore.

#### `delay`
- When delay is specified, Trickster will wait for a random time between the bounds before returning the response.
- Delay is an array of two floats - min and max delay, eg. `[0.5, 1.3]`.
- Default `none`