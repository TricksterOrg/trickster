"""User-configurable routing."""

from __future__ import annotations

import re
import json
import uuid
import random
import enum
import time
from collections import OrderedDict

import flask

from trickster import RouteConfigurationError
from trickster.auth import Auth
from trickster.input import IncommingRequest

from typing import Optional, Dict, Any, List, Iterable


class Delay:
    """Delay allows you to se arbitrary time to wait before response is returned."""

    def __init__(self, min_delay: float = 0.0, max_delay: float = 0.0):
        if min_delay > max_delay:
            raise RouteConfigurationError(
                f'Minimum delay cannot be longer than maximum delay: {min_delay} > {max_delay}'
            )
        self.min_delay = min_delay
        self.max_delay = max_delay

    def serialize(self) -> Optional[List[float]]:
        """Convert Delay to json."""
        if self.min_delay == self.max_delay == 0.0:
            return None
        return [self.min_delay, self.max_delay]

    def wait(self) -> None:
        """Put program to sleep for random amount of time withing the specified range."""
        wait_time = random.uniform(self.min_delay, self.max_delay)
        time.sleep(wait_time)

    @classmethod
    def deserialize(cls, data: List[float]) -> Delay:
        """Convert json to Delay."""
        if data:
            return cls(*data)
        return cls()


class ResponseSelectionStrategy(enum.Enum):
    """Strategy of how to select a Response from list of responses."""

    cycle = 'cycle'
    random = 'random'
    greedy = 'greedy'

    def select_response_cycle(self, responses: List[Response]) -> Optional[Response]:
        """Select proper response from list of candidate responses.

        Consumes responses in order of definition. Cycles through items one by one.
        """
        candidate = None

        for response in responses:
            if response.is_active and (candidate is None or response.used_count < candidate.used_count):
                candidate = response
        return candidate

    def select_response_random(self, responses: List[Response]) -> Optional[Response]:
        """Select proper response from list of candidate responses.

        Selects random response from all available.
        """
        population = [r for r in responses if r.is_active]
        weights = [r.weight for r in population]
        result = random.choices(population=population, weights=weights, k=1)
        return result[0] if result else None

    def select_response_greedy(self, responses: List[Response]) -> Optional[Response]:
        """Select proper response from list of candidate responses.

        Consumes responses in order of definition until the first one is exhausted,
        then starts consuming the next in the row.
        """
        for response in responses:
            if response.is_active:
                return response
        return None

    def select_response(self, responses: Iterable[Response]) -> Optional[Response]:
        """Select proper response from list of candidate responses."""
        method_name = f'select_response_{self.value}'
        method = getattr(self, method_name)
        return method(responses)

    def serialize(self) -> str:
        """Convert ResponseSelectionStrategy to json."""
        return self.value

    @classmethod
    def deserialize(cls, method: Optional[str] = None) -> ResponseSelectionStrategy:
        """Convert json to ResponseSelectionStrategy."""
        return cls(method or 'greedy')


class Response:
    """Container for predefined response."""

    def __init__(
        self,
        id: str,
        body: Any,
        delay: Delay,
        headers: Optional[Dict[str, Any]] = None,
        status: int = 200,
        repeat: Optional[int] = None,
        weight: float = 0.5
    ) -> None:
        self.id = id
        self.body = body
        self.headers = headers or {}
        self.status = status
        self.repeat = repeat
        self.weight = weight
        self.delay = delay
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
            'id': self.id,
            'is_active': self.is_active,
            'status': self.status,
            'used_count': self.used_count,
            'weight': self.weight,
            'headers': self.headers,
            'repeat': self.repeat,
            'delay': self.delay.serialize(),
            'body': self.body
        }

    def use(self) -> None:
        """Increases usage counter of Response."""
        self.used_count += 1

    @property
    def is_active(self) -> bool:
        """Return True if response has some uses left."""
        return self.repeat is None or self.repeat > self.used_count

    def wait(self) -> None:
        """Sleep for time specified in the response."""
        self.delay.wait()

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> Response:
        """Convert json to Response."""
        delay = Delay.deserialize(data.pop('delay', None))

        if 'headers' in data:
            headers = data.pop('headers')
        elif not isinstance(data['body'], str):
            headers = {'content-type': 'application/json'}
        else:
            headers = {}

        return cls(delay=delay, headers=headers, **data)


class Route:
    """Route is a pair of request arguments and all possible reponses."""

    def __init__(
        self,
        id: str,
        responses: OrderedDict[str, Response],
        response_selection: ResponseSelectionStrategy,
        path: re.Pattern,
        auth: Auth,
        method: str = 'GET'
    ):
        self.id = id
        self.responses = responses
        self.response_selection = response_selection
        self.method = method
        self.path = path
        self.auth = auth
        self.used_count = 0

    def serialize(self) -> Dict[str, Any]:
        """Convert Route to JSON."""
        return {
            'id': self.id,
            'response_selection': self.response_selection.serialize(),
            'auth': self.auth.serialize(),
            'method': self.method,
            'path': self.path.pattern,
            'used_count': self.used_count,
            'responses': [response.serialize() for response in self.responses.values()]
        }

    def get_response(self, response_id: str) -> Optional[Response]:
        """Get a Response by its id."""
        for response in self.responses.values():
            if response.id == response_id:
                return response
        return None

    @classmethod
    def _create_responses(cls, responses: List[Dict[str, Any]]) -> OrderedDict[str, Response]:
        """Create Response objects from json."""
        result = OrderedDict()
        for response in responses:
            if 'id' not in response:
                response['id'] = str(uuid.uuid4())
            elif response['id'] in result:
                raise RouteConfigurationError(f'Duplicate response id {response["id"]}.')

            result[response['id']] = Response.deserialize(response)
        return result

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> Route:
        """Convert json to Route."""
        id = data.pop('id')
        auth = Auth.deserialize(data.pop('auth', None))
        path = re.compile(data.pop('path', None))
        response_selection = ResponseSelectionStrategy.deserialize(data.pop('response_selection', None))
        responses = cls._create_responses(data.pop('responses'))

        return cls(
            id=id,
            responses=responses,
            response_selection=response_selection,
            path=path,
            auth=auth,
            **data
        )

    def use(self, response: Optional[Response]) -> None:
        """Increment use counter of this Route and given Response."""
        self.used_count += 1
        if response:
            response.use()

    def match(self, request: IncommingRequest) -> bool:
        """Return True, if this request specification matches given InputRequest."""
        return self._match_method(request.method) and self._match_path(request.path)

    def _match_method(self, method: Optional[str]) -> bool:
        """Return True, if this requests HTTP method matches given InputRequest."""
        return self.method in [None, method]

    def _match_path(self, path: str) -> bool:
        """Return True, if this requests path matches given InputRequest."""
        return bool(self.path.match(path))

    def select_response(self) -> Optional[Response]:
        """Select response from list of responses."""
        return self.response_selection.select_response(self.responses.values())

    def authenticate(self, request: IncommingRequest) -> None:
        """Check if Request if properly authenticated."""
        self.auth.authenticate(request)


class Router:
    """Custom request/response router."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Remove all custom routes."""
        self.routes: OrderedDict[str, Route] = OrderedDict()

    def _validate_route_ids(self, route_ids: List[Optional[str]]) -> None:
        """Check that there are no duplicate route id."""
        for route_id in route_ids:
            if route_id is None:
                continue
            if route_id in self.routes:
                raise RouteConfigurationError(f'Route id "{route_id}"" already exists.')
            if route_ids.count(route_id) > 1:
                raise RouteConfigurationError(f'Duplicate route id "{route_id}".')

    def _generate_route_id(self) -> str:
        """Generate route id."""
        while True:
            route_id = str(uuid.uuid4())
            if route_id not in self.routes:
                return route_id

    def _add_validated_route(self, route: Dict[str, Any]) -> Route:
        """Add route assuming its id was already validated."""
        if 'id' not in route:
            route['id'] = self._generate_route_id()

        new_route = Route.deserialize(route)
        self.routes[new_route.id] = new_route
        return new_route

    def add_route(self, route: Dict[str, Any]) -> Route:
        """Add custom request and matching responses."""
        self._validate_route_ids([route.get('id')])
        return self._add_validated_route(route)

    def add_routes(self, routes: List[Dict[str, Any]]) -> List[Route]:
        """Add multiple custom requests and matching responses."""
        self._validate_route_ids([route.get('id') for route in routes])
        result = []
        for route in routes:
            result.append(self._add_validated_route(route))
        return result

    def get_route(self, route_id: str) -> Optional[Route]:
        """Get Route by its id."""
        return self.routes.get(route_id, None)

    def match(self, incomming_request: IncommingRequest) -> Optional[Route]:
        """Find matching request and return apropriet response or None if none found."""
        for route in self.routes.values():
            if route.match(incomming_request):
                return route
        return None

    def serialize(self) -> List[Dict[str, Any]]:
        """Convert Router to dictionary suitable for sending as api response."""
        return [route.serialize() for route in self.routes.values()]
