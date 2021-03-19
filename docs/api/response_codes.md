---
title: Response codes
layout: default
nav_order: 3
parent: API
---


# Response codes
These are the common HTTP codes, API returns:

1. TOC
{:toc}

## 200 OK
Returned when Trickster successfully processed your request. Response body always contains JSON with response data.

> Example: `200 OK` is returned from `GET /internal/match_route` when a Route was found. The body contains the matched Route.

## 201 Created
Returned when Trickster successfully processed your request and created new item or updated old one. Response body always contains json with the created resource.

> Example: `201 Created` is returned from `POST /internal/routes` which creates new Route . The body contains the newly created Route.

## 204 No Content
Returned when Trickster successfully processed your request but there are no data to be returned. Response body will always be empty.

> Example: `204 No Content` is returned from `DELETE /internal/routes/<route_id>` which removes a Route.

## 400 Bad Request
Returned when Trickster couldn't process your request because it contained malformed data. Body contains JSON with details about the error: `{"error": "Bad Request", "message": "Error message."}`

> Example: `400 Bad Request` is returned from `POST /internal/routes` when you send a payload which doesn't contain all required fields.

## 404 Not Found
Returned when Trickster couldn't find required resource or url. Body contains JSON with details about the error: `{"error": "Not Found", "message": "Error message."}`

> Example `404 Not Found` is returned when you call url that doesn't exist or when you call `GET /internal/routes/not_existing_route_id`.

## 409 Duplicate
Returned when Trickster could not create a resource because it already exists. Body contains JSON with details about the error: `{"error": "Duplicate", "message": "Error message."}`

> Example: `409 Duplicate` when you call `POST /internal/routes` with Route id that already exists.

## 500 Internal Server Error
Returned when Trickster encountered unknown error. Body contains JSON with details about the error: `{"error": "Internal Server Error", "message": "Error message."}`

> Example: Hopefully you will never see this error from Trickster.