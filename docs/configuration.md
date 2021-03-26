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
If you run Trickster in a docker container, you can change the prefix of internal endpoints by setting the `TRICKSTER_INTERNAL_PREFIX` using [any method supported by docker](https://docs.docker.com/engine/reference/commandline/run/#set-environment-variables--e---env---env-file). Eg. `docker run -p 8080:8080 -r TRICKSTER_INTERNAL_PREFIX=/api tesarekjakub/trickster`

### Docker-compose
To set internal prefix in docker-compose, use the `environment` directive:

```yml
mock-service:
    image: tesarekjakub/trickster:latest
    ports: ["8080:8080"]
    environment:
      TRICKSTER_INTERNAL_PREFIX: "/api"
```