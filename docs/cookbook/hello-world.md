---
title: Hello World!
layout: default
nav_order: 1
parent: cookbook
---

# Model
{: .no_toc }

This section describes entities that live inside Trickster, their properties and purpose.

# Hello World!
{: .no_toc }

In this example we will

1. TOC
{:toc}

## Check if Trickster is running
We will use [health endpoint](https://jakubtesarek.github.io/trickster/api/endpoints.html#get-internalhealth).

Create python file or run this code from console:

```python
import requests

r = requests.get('http://localhost:5000/internal/health')
print(r.json)
assert r.status_code == 200
```

When you run this program, it should print out `{'status': 'ok'}`. If it does, congratulations, Trickster is running. If it prints anything else, you need to investigate further.

Usually there are two types of problems that may occur.

- If you see that `requests.exceptions.ConnectionError` was raised, there was a problem connecting to Trickster. Try to restart it. Check that you don't have a typo in the url and there's nothing blocking port 5000.
- If you see `AssertionError`, it probably means that Trickster didn't return http code 200. If this happens, `r.json` contains [Error object](https://jakubtesarek.github.io/trickster/api/model.html#error) with details about the problem.


## Create and call a Route
Let's create our first route and call it. We will call url `/hello_world` with this code:

```python
import requests

r = requests.get('http://localhost:5000/hello_world')
print(r.json)
```

If you call it now, you will recieve `404 Not Found` and error message:

```json
{
    "error": "Not Found",
    "message": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
}
```

We need to tell Trickster that we want him to resolve this url and what it should return. To do so, we have define a [Route](https://jakubtesarek.github.io/trickster/api/model.html#route) with a [Response](https://jakubtesarek.github.io/trickster/api/model.html#response). You can check the documentation for all the available options, for now we'll send only the minimal configuration.

```python
import requests

r = requests.post('http://localhost:5000/internal/routes', json={
    'path': '/hello_world',
    'responses': [
        {'body': 'Hello World!'}
    ]
})
```

This creates new Route that will match any GET request on path `/hello_world` and will respond with string `Hello World!`. If you didn't get any error, the Route was created. To be sure, you can list all Routes:

```python
import requests

r = requests.get('http://localhost:5000/internal/routes')
print(r.json)
```
You should get something like this:

```json
[
    {
        "id": "24f7f7c2-a2e4-415b-bb55-aaa0c85b76fd",
        "used_count": 0,
        "auth": null,
        "method": "GET",
        "path": "/hello_world",
        "response_selection": "greedy",
        "responses": [
            {
                "id": "0b0c65a6-37ea-48b7-96e1-015d3fe23cb6",
                "body": "Hello World!",
                "delay": null,
                "headers": {},
                "is_active": true,
                "repeat": null,
                "status": 200,
                "used_count": 0,
                "weight": 0.5
            }
        ]
    }
]
```

You responses will look slightly differently. But it's important that you got a list containing one Route which contains one Response.

Now you can finally call the `/hello_world` url:

```python
import requests

r = requests.get('http://localhost:5000/hello_world')
print(r.text)
```

and receive:

```
Hello World!
```
