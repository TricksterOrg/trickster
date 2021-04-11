"""Routing module provides functionality to configure routes and responses."""

from __future__ import annotations

import json
import random
import time
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import flask

from trickster import TricksterException


class RouteConfigurationError(TricksterException, ValueError):
    """Raised when route could not be configured because of value error."""

    http_code: int = 400


class DuplicateRouteError(RouteConfigurationError):
    """Raised when route could not be configured because there is a duplicatit in ids."""

    http_code: int = 409


class MissingRouteError(RouteConfigurationError):
    """Raised when route could not be configured because it doesn't exist."""

    http_code: int = 404


class AuthenticationError(TricksterException):
    """Exception raised when user could not be authenticated."""


class Delay:
    """Delay allows you to se arbitrary time to wait before response is returned."""

    def __init__(self, min_delay: float = 0.0, max_delay: float = 0.0):
        if min_delay > max_delay:
            raise RouteConfigurationError(
                f'Minimum delay cannot be longer than maximum delay: {min_delay} > {max_delay}'
            )
        self.min_delay = min_delay
        self.max_delay = max_delay

    def serialize(self) -> Union[Optional[List[float]], float]:
        """Convert Delay to json."""
        if self.min_delay == self.max_delay:
            return self.min_delay  # Express delay as one number
        return [self.min_delay, self.max_delay]

    def wait(self) -> None:
        """Put program to sleep for random amount of time withing the specified range."""
        wait_time = random.uniform(self.min_delay, self.max_delay)
        time.sleep(wait_time)

    @classmethod
    def deserialize(cls, data: Union[Optional[List[float]], float]) -> Delay:
        """Convert json to Delay."""
        if data is None:
            return cls(0.0, 0.0)
        if isinstance(data, (int, float)):
            return cls(data, data)
        return cls(*data)


class Response:
    """Container for predefined response."""

    def __init__(self, body: Any, delay: Delay, headers: Optional[Dict[str, Any]] = None, status: int = 200) -> None:
        self.body = body
        self.delay = delay
        self.headers = headers or {}
        self.status = status
        self.used_count = 0

    @property
    def serialized_body(self) -> str:
        """Convert specified response body to string."""
        if isinstance(self.body, str):
            return self.body
        else:
            return json.dumps(self.body)

    def as_flask_response(self) -> flask.Response:
        """Convert Request to flask.Response suitable to return from an endpoint."""
        return flask.Response(
            response=self.serialized_body,
            status=self.status,
            headers=self.headers
        )

    def serialize(self) -> Dict[str, Any]:
        """Convert Response to json."""
        return {
            'status': self.status,
            'used_count': self.used_count,
            'headers': self.headers,
            'delay': self.delay.serialize(),
            'body': self.body
        }

    def use(self) -> None:
        """Increases usage counter of Response."""
        self.used_count += 1

    def wait(self) -> None:
        """Sleep for time specified in the response."""
        self.delay.wait()

    @classmethod
    def deserialize(cls: Type[ResponseType], data: Dict[str, Any]) -> ResponseType:
        """Convert json to Response."""
        delay = Delay.deserialize(data.pop('delay', None))

        if 'headers' in data:
            headers = data.pop('headers')
        elif not isinstance(data['body'], str):
            headers = {'content-type': 'application/json'}
        else:
            headers = {}

        return cls(delay=delay, headers=headers, **data)


# https://stackoverflow.com/questions/58986031/type-hinting-child-class-returning-self/58986197#58986197
ResponseType = TypeVar('ResponseType', bound=Response)
