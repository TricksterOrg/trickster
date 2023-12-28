"""Internal router used to match client defined routes."""

from __future__ import annotations

import functools
import uuid
import http

from fastapi import Depends
from pydantic import BaseModel, Field
from starlette.requests import Request

from trickster.config import Config, get_config
from trickster.model import Route, RouteMatch, Response, ResponseSelector
import os
import threading

class Router(BaseModel):
    """Router containing routes that can match user request."""

    error_response_selector: ResponseSelector = Field(
        default=ResponseSelector.RANDOM, description='Response selector for error response'
    )
    error_responses: list[Response] = Field(default_factory=list, description='List of error responses')
    routes: list[Route] = Field(default_factory=list, description='All configured routes')

    def match(self, request: Request) -> RouteMatch | None:
        """Find a route that matches request and return it with matched parameters."""
        for route in self.routes:
            if matched_attributes := route.match(request):
                return RouteMatch(
                    route=route,
                    http_method=matched_attributes[0],
                    path_params=matched_attributes[1]
                )
        return None

    def get_routes(self) -> list[Route]:
        """Get all configured routes."""
        return self.routes

    def add_route(self, route: Route) -> None:
        """Add new route."""
        self.routes.append(route)

    def delete_route(self, route: Route) -> None:
        """Delete configured route."""
        self.routes.remove(route)

    def delete_routes(self) -> None:
        """Delete all configured routes."""
        self.routes = []

    def get_route_by_id(self, route_id: uuid.UUID) -> Route | None:
        """Get route by id."""
        for route in self.routes:
            if route.id == route_id:
                return route
        return None

    def get_error_responses(self, status_code: http.HTTPStatus | None = None) -> list[Response]:
        """Get configured error response by their status code or all if status code not provided."""
        return [r for r in self.error_responses if r.status_code == status_code or not status_code]

    def get_error_response(self, status_code: http.HTTPStatus) -> None | Response:
        """Get single error response by its status code.

        If there are multiple error responses with the required status code, Router uses configured ResponseSelector
        to select one.
        """
        if error_response := self.get_error_responses(status_code):
            return self.error_response_selector.select_response(error_response)
        return None

    def add_error_response(self, error_response: Response) -> None:
        """Add new error error response."""
        self.error_responses.append(error_response)

    def get_error_response_by_id(self, response_id: uuid.UUID) -> None | Response:
        """Get configured error response by its ID."""
        for error_response in self.error_responses:
            if error_response.id == response_id:
                return error_response
        return None

    def delete_error_response(self, error_response: Response) -> None:
        """Delete configured error response."""
        self.error_responses.remove(error_response)


@functools.lru_cache(typed=False)
def get_router(config: Config = Depends(get_config)) -> Router:
    """Get a router."""
    error_responses = [Response(**response.model_dump()) for response in config.settings.error_responses]
    return Router(error_responses=error_responses)
