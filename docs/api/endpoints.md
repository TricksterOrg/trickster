---
title: Endpoints
layout: default
nav_order: 1
parent: API
---


# Endpoints
{: .no_toc }

This section describes all endpoints from internal API.

1. TOC
{:toc}


## `GET /internal/health`
Returns status of Trickster service.

Use this endpoint if you want to check if Trickster is running.

### Response
{: .no_toc }

Returns `200 Ok`. Body contains `{"status": "ok"}`. If this endpoints return anything else, Trickster is not
running properly. Check if Trickster is running, if it logs errors, your network etc.


## `GET /internal/routes`
Get list of all configured Routes.

### Response
{: .no_toc }

Returns `200 Ok`. Body contains list of [Route objects](/trickster/api/model.html#route).


## `DELETE /internal/routes`
Remove all configured routes.

### Response:
{: .no_toc }

Returns `204 No Content`. Body is empty.


## `POST /internal/routes`
Add new route.

### Payload
{: .no_toc }

Single [Route object](/trickster/api/model.html#route). Payload is validated using [Route JSON Schema](https://raw.githubusercontent.com/JakubTesarek/trickster/main/trickster/schemas/route.schema.json).

### Response
{: .no_toc }

On success returns `200 OK`, body contains the newly created [Route object](/trickster/api/model.html#route).
Otherwise returns an [error response](/trickster/api/response-codes).


## `GET /internal/routes/<route_id:str>`
Get a single Route by it's id.

### Response
{: .no_toc }

If the Route is found, returns `200 OK`. Body contains single configured [Route object](/trickster/api/model.html#route).
Otherwise returns an [error response](/trickster/api/response-codes).


## `POST /internal/routes/<route_id:str>`
Configure new Route.

### Payload
{: .no_toc }

Single [Route object](/trickster/api/model.html#route). Payload is validated using [Route JSON Schema](https://raw.githubusercontent.com/JakubTesarek/trickster/main/trickster/schemas/route.schema.json).

### Response
{: .no_toc }

If the Route was successfully created, returns `200 OK`. Body contains the newly created [Route object](/trickster/api/model.html#route). Otherwise returns an [error response](/trickster/api/response-codes).


## `PUT /internal/routes/<route_id:str>`
Replaces a previously configured Route with new data.

Use this endpoint if you previously created a Route and want to re-create it with new data.

The `route_id` in url represents the `id` of the Route that will be replaced. The `id` inside the payload is the new `id`. This way, you can change `id` of a Route.

You always have to provide the `route_id` in url. The `id` in payload is optional. If you don't want to change it, it's best if you don't send it at all and the Route will preserve the original `id`.

Note that this endpoint behaves differently from deleting and inserting the Route. If you remove the Route and then you insert it, it will be put at the end. It means that when Trickster attempts to match a route, the newly created Route will be tested last. In constrast, if you update the Route using this endpoint, it will keep it's original position in the list.

### Payload
{: .no_toc }

Single [Route object](/trickster/api/model.html#route). Payload is validated using [Route JSON Schema](https://raw.githubusercontent.com/JakubTesarek/trickster/main/trickster/schemas/route.schema.json).

### Response
{: .no_toc }

If the Route was found and successfully modified, returns `200 OK`. Body contains the newly configured [Route objects](/trickster/api/model.html#route). Otherwise returns an [error response](/trickster/api/response-codes).


## `DELETE /internal/routes/<route_id:str>`
Remove previously created Route.

### Response
{: .no_toc }

If the Route was found and successfully removed, returns `204 No Content` and empty body. Otherwise returns an [error response](/trickster/api/response-codes).


## `POST /internal/match_route`
Finds a Route that matches provided request.

Use this endpoint if you previosly configured some Routes and you want to know which one, if any, will match your request.

### Payload
{: .no_toc }

Single [Request object](/trickster/api/model.html#request). Payload is validated using [Request JSON Schema](https://raw.githubusercontent.com/JakubTesarek/trickster/main/trickster/schemas/request.schema.json).

### Response
{: .no_toc }

If the Request was matched by any of the configured Routes it returns `200 OK` and the corresponding [Route object](/trickster/api/model.html#route). Otherwise returns an [error response](/trickster/api/response-codes).


## `GET /internal/routes/<string:route_id>/responses/<string:response_id>`
Returns a single configured Response object from a Route given by id.

Use this endpoint if you previously configured a Route with Responses and you want to find details about one of the Responses. This is useful, for example, when you want to know how many times if was returned.

### Response
{: .no_toc }

If the Request and Response was found, it returns `200 OK` and the corresponding [Response object](/trickster/api/model.html#response). Otherwise returns an [error response](/trickster/api/response-codes).