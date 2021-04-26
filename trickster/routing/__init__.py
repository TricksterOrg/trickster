"""Routing module provides functionality to configure routes and responses."""

from __future__ import annotations

import json
import random
import time
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import flask

import jsonpath_ng as jsonpath

from trickster import TricksterException
from trickster.validation import match_shema


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

    http_code: int = 401

    def serialize(self) -> Dict[str, Any]:
        """Convert error to json."""
        return {
            'error': 'Unauthorized',
            'message': str(self),
            'code': self.http_code
        }


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


class ResponseContext:
    """Context containing information about current request that can be used to render response."""

    def __init__(self) -> None:
        self.variables: Dict[str, Any] = {}

    def __setitem__(self, name: str, value: Any) -> None:
        """Set item to context."""
        if not isinstance(value, (str, int, list, dict)):
            value = value.serialize()
        self.variables[name] = value

    def __getitem__(self, name: str) -> Any:
        """Get item from context."""
        return self.variables[name]

    def get(self, key: str) -> Any:
        """Get variable from context by jsonpath."""
        expr = jsonpath.parse(key)
        results = expr.find(self.variables)

        if len(results) > 1:
            return [r.value for r in results]
        elif len(results) == 1:
            return results[0].value
        else:
            return None


class ResponseBody:
    """Body of response."""

    def __init__(self, content: Any):
        self.content = content

    def as_flask_response(self, context: ResponseContext) -> str:
        """Convert response body to string within given context."""
        return self.content

    def serialize(self) -> Any:
        """Convert response body to json."""
        return self.content

    @property
    def default_headers(self) -> Dict[str, str]:
        """Get default headers of response."""
        return {}

    @classmethod
    def deserialize(cls, data: Any) -> ResponseBody:
        """Convert json to response body."""
        if isinstance(data, str):
            return ResponseBody(data)
        else:
            return JsonResponseBody(data)


class JsonResponseBody(ResponseBody):
    """Json body of response."""

    def __init__(self, content: Any):
        self._validate_attribute(content)
        super().__init__(content)

    @property
    def default_headers(self) -> Dict[str, str]:
        """Get default headers of response."""
        return {'content-type': 'application/json'}

    def as_flask_response(self, context: ResponseContext) -> str:
        """Convert response body to string within given context."""
        return json.dumps(self._render_attribute(self.content, context))

    def _is_dynamic_attribute(self, attr: Dict[str, Any]) -> bool:
        """Return True if given attribute should be evaluated within context."""
        return match_shema(attr, 'dynamic_attribute.schema.json')

    def _render_attribute(self, attr: Any, context: ResponseContext) -> Any:
        """Evaluate given attribute within context."""
        if self._is_dynamic_attribute(attr):
            return context.get(attr['$ref'])
        elif isinstance(attr, dict):
            return {k: self._render_attribute(v, context) for k, v in attr.items()}
        elif isinstance(attr, list):
            return [self._render_attribute(v, context) for v in attr]
        else:
            return attr

    def _validate_attribute(self, attr: Any) -> None:  # noqa: C901
        """Recursively validate given attribute."""
        # TODO: This method is too similiar to `_render_attribute`. Refactor!
        if self._is_dynamic_attribute(attr):
            try:
                jsonpath.parse(attr['$ref'])
            except Exception as e:
                raise RouteConfigurationError(f'Invalid jsonpath query "{attr["$ref"]}": {e}') from e
        elif isinstance(attr, dict):
            for v in attr.values():
                self._validate_attribute(v)
        elif isinstance(attr, list):
            for v in attr:
                self._validate_attribute(v)


class Response:
    """Container for predefined response."""

    def __init__(
        self,
        body: ResponseBody,
        delay: Delay,
        headers: Optional[Dict[str, Any]] = None,
        status: int = 200
    ) -> None:
        self.body = body
        self.delay = delay
        self.headers = headers or {}
        self.status = status
        self.used_count = 0

    def as_flask_response(self, context: ResponseContext) -> flask.Response:
        """Convert Request to flask.Response suitable to return from an endpoint."""
        return flask.Response(
            response=self.body.as_flask_response(context),
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
            'body': self.body.serialize()
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
        body = ResponseBody.deserialize(data.pop('body', None))
        headers = data.pop('headers', body.default_headers)

        return cls(delay=delay, headers=headers, body=body, **data)


# https://stackoverflow.com/questions/58986031/type-hinting-child-class-returning-self/58986197#58986197
ResponseType = TypeVar('ResponseType', bound=Response)
