---
title: Configuration
layout: default
nav_order: 2
---

# Configuration
{: .no_toc }

1. TOC
{:toc}


Trickster doesn't need any configuration to run. You can just [install it and run it](/trickster/installation.html). But if you wish, there are things you can customize.

## Port
By default Trickster binds to port `8080`.

### CLI
If you run Trickster as local python application using `trickster run`, you can change the port it bind to using `-p/--port` argument, eg. `trickster run -p 5000`.

Changing the port using the environment variable `TRICKSTER_PORT` is also possible but not recommended. If you set both the environment variable and CLI argument, the CLI argument takes precedence.

### Docker
Trickster docker container exposes port `8080`. But to make it available on your localhost image, you still have to [expose it when you start the container](https://docs.docker.com/engine/reference/commandline/run/#publish-or-expose-port--p---expose): `docker run -p 8080:8080 tesarekjakub/trickster`. You can change the port by mapping the internal `8080` port to another local port, eg. `docker run -p 5000:8080 tesarekjakub/trickster`

### Docker-compose
It is common practice to include Trickster in the `docker-compose.yml` for local development. You can expose the port using the `ports` directive:

```yml
mock-service:
    image: tesarekjakub/trickster:latest
    ports: ["5000:8080"]
```

## Internal prefix
Trickster provides the internal API on `/internal`. Eg. the endpoint to add a new Route lives on `POST http://127.0.0.1:8080/internal/routes`. This can cause conflicts with your own routes that use prefix `/internal` so you may want to change it.

> If there is a conflict in path between internal endpoints and custom Routes, internal endpoints take precedence.

Internal prefix always has to start with slash, not end with slash and contain only characters that are valid in url. These are valid examples: `/api`, `/_`, `/internal/api`.

### CLI
You can configure the internal prefix using the `-x/--prefix` argument, eg. `trickster run -x /api`.

Changing the internal prefix using the environment variable `TRICKSTER_INTERNAL_PREFIX` is also possible but not recommended. If you set both the environment variable and CLI argument, the CLI argument takes precedence.

### Docker
If you run Trickster in a docker container, you can change the prefix of internal endpoints by setting the `TRICKSTER_INTERNAL_PREFIX` using [any method supported by docker](https://docs.docker.com/engine/reference/commandline/run/#set-environment-variables--e---env---env-file). Eg. `docker run -p 8080:8080 -e TRICKSTER_INTERNAL_PREFIX=/api tesarekjakub/trickster`

### Docker-compose
To set internal prefix in docker-compose, use the `environment` directive:

```yml
mock-service:
    image: tesarekjakub/trickster:latest
    ports: ["8080:8080"]
    environment:
      TRICKSTER_INTERNAL_PREFIX: "/api"
```

## Default routes
Trickster allows you to set defalt routes that will be loaded when in starts. You may provide them as a json file containing a list of Routes. The format of Route is equal to [POST Route endpoint](/trickster/api/endpoints.html#post-internalroutes).

```json
[
    {
	"path": "/endpoint1",
	"responses": [
	    {
	        "body": "response1"
	    }
        ]

    },
    {
        "path": "/endpoint2",
        "responses": [
            {
                "body": "response2"
            }
        ]
    }
]
```

### CLI
You can configure internal routes by providing path to json file using the `-r/--routes` argument, eg. `trickster run -r routes.json`.

### Docker
If you use docker, you may provide path to default routes using the environmen variable `TRICKSTER_ROUTES`. You also have to mount the file (or directory containing the file) inside the container.

Eg.  `docker run --mount type=bind,source="$(pwd)"/test.json,target=/routes.json,readonly -e TRICKSTER_ROUTES=/routes.json`

### Docker-compose

```yml
mock-service:
    image: tesarekjakub/trickster:latest
    ports: ["8080:8080"]
    environment:
      TRICKSTER_ROUTES: "/routes.json"
    volumes:
      - ${PWD}/routes.json:/routes.json
```
