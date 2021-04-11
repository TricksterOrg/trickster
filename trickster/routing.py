"""User-configurable routing."""

from __future__ import annotations

import enum
import json
import random
import re
import time
import uuid
from typing import Any, Dict, Iterable, List, Optional, Type, TypeVar, Union

import flask

from trickster import DuplicateRouteError, MissingRouteError, RouteConfigurationError
from trickster.auth import Auth
from trickster.collections import IdItem, IdList
from trickster.input import IncomingRequest


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


class ResponseSelectionStrategy(enum.Enum):
    """Strategy of how to select a RouteResponses from list of responses."""

    cycle = 'cycle'
    random = 'random'
    greedy = 'greedy'

    def select_response_cycle(self, responses: List[RouteResponse]) -> Optional[RouteResponse]:
        """Select proper response from list of candidate responses.

        Consumes responses in order of definition. Cycles through items one by one.
        """
        candidate = None

        for response in responses:
            if response.is_active and (candidate is None or response.used_count < candidate.used_count):
                candidate = response
        return candidate

    def select_response_random(self, responses: List[RouteResponse]) -> Optional[RouteResponse]:
        """Select proper response from list of candidate responses.

        Selects random response from all available.
        """
        population = [r for r in responses if r.is_active]
        weights = [r.weight for r in population]
        result = random.choices(population=population, weights=weights, k=1)
        return result[0] if result else None

    def select_response_greedy(self, responses: List[RouteResponse]) -> Optional[RouteResponse]:
        """Select proper response from list of candidate responses.

        Consumes responses in order of definition until the first one is exhausted,
        then starts consuming the next in the row.
        """
        for response in responses:
            if response.is_active:
                return response
        return None

    def select_response(self, responses: Iterable[RouteResponse]) -> Optional[RouteResponse]:
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


class RouteResponse(Response, IdItem):
    """Container for predefined response in Route."""

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
        Response.__init__(self, body, delay, headers, status)
        IdItem.__init__(self, id)
        self.repeat = repeat
        self.weight = weight

    def serialize(self) -> Dict[str, Any]:
        """Convert Response to json."""
        return {
            **Response.serialize(self),
            **IdItem.serialize(self),
            'is_active': self.is_active,
            'weight': self.weight,
            'repeat': self.repeat,
        }

    @property
    def is_active(self) -> bool:
        """Return True if response has some uses left."""
        return self.repeat is None or self.repeat > self.used_count


class Route(IdItem):
    """Route is a pair of request arguments and all possible reponses."""

    def __init__(
        self,
        id: str,
        responses: Iterable[RouteResponse],
        response_selection: ResponseSelectionStrategy,
        path: re.Pattern,
        auth: Auth,
        method: str = 'GET'
    ):
        super().__init__(id)
        self.response_selection = response_selection
        self.method = method
        self.path = path
        self.auth = auth
        self.used_count = 0
        self.responses: IdList[RouteResponse] = IdList()

        try:
            for response in responses:
                self.responses.add(response)
        except KeyError:
            raise DuplicateRouteError(f'Duplicate response id {response.id}.')

    def serialize(self) -> Dict[str, Any]:
        """Convert Route to JSON."""
        return {
            **super().serialize(),
            'response_selection': self.response_selection.serialize(),
            'auth': self.auth.serialize(),
            'method': self.method,
            'path': self.path.pattern,
            'used_count': self.used_count,
            'responses': self.responses.serialize(),
            'is_active': self.is_active
        }

    def get_response(self, response_id: str) -> Optional[RouteResponse]:
        """Get a RouteResponse by its id."""
        return self.responses.get(response_id)

    @classmethod
    def _create_responses(cls, responses: List[Dict[str, Any]]) -> List[RouteResponse]:
        """Create RouteResponse objects from json."""
        result = []
        for response in responses:
            if 'id' not in response:
                response['id'] = str(uuid.uuid4())
            result.append(RouteResponse.deserialize(response))
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

    def use(self, response: RouteResponse = None) -> None:
        """Increment use counter of this Route and given RouteResponse."""
        self.used_count += 1
        if response:
            response.use()

    def match(self, request: IncomingRequest) -> bool:
        """Return True, if this request specification matches given request and Route is active."""
        return all([
            self._match_method(request.method),
            self._match_path(request.path),
            self.is_active
        ])

    def _match_method(self, method: Optional[str]) -> bool:
        """Return True, if this requests HTTP method matches given InputRequest."""
        return self.method in [None, method]

    def _match_path(self, path: str) -> bool:
        """Return True, if this requests path matches given InputRequest."""
        return bool(self.path.match(path))

    def select_response(self) -> Optional[RouteResponse]:
        """Select response from list of responses."""
        return self.response_selection.select_response(self.responses)

    def authenticate(self, request: IncomingRequest) -> None:
        """Check if Request if properly authenticated."""
        self.auth.authenticate(request)

    @property
    def is_active(self) -> bool:
        """Return True if Route has at least one active RouteResponse."""
        for response in self.responses:
            if response.is_active:
                return True
        return False


class Router:
    """Custom request/response router."""

    def __init__(self) -> None:
        self.reset()

    def reset(self, routes: Optional[List[Dict[str, Any]]] = None) -> None:
        """Replace all custom routes."""
        self.routes: IdList[Route] = IdList()
        if routes:
            for route in routes:
                self.add_route(route)

    def _generate_route_id(self) -> str:
        """Generate route id."""
        while (route_id := str(uuid.uuid4())) in self.routes:
            # It's virtually impossibe to generate the same uuid twice
            continue  # pragma: no cover
        return route_id

    def _set_route_id(self, route: Dict[str, Any], route_id: str = None) -> None:
        """Set route id if it doesn't already exist. Generate id if not set."""
        route.setdefault('id', route_id or self._generate_route_id())

    def add_route(self, route: Dict[str, Any]) -> Route:
        """Add custom request and matching responses."""
        self._set_route_id(route)
        route_object = Route.deserialize(route)
        try:
            self.routes.add(route_object)
        except KeyError:
            raise DuplicateRouteError(f'Route id "{route_object.id}" already exists.')
        return route_object

    def get_route(self, route_id: str) -> Optional[Route]:
        """Get Route by its id."""
        return self.routes.get(route_id)

    def remove_route(self, route_id: str) -> None:
        """Remove Route by its id."""
        self.routes.remove(route_id)

    def update_route(self, route: Dict[str, Any], route_id: str) -> Route:
        """Update route with completely new data."""
        self._set_route_id(route, route_id)
        if route_id != route['id'] and route['id'] in self.routes:
            raise DuplicateRouteError(
                f'Cannot change route id "{route_id}" to "{route["id"]}". Route id "{route["id"]}" already exists.'
            )

        route_object = Route.deserialize(route)
        try:
            self.routes.replace(route_id, route_object)
        except KeyError:
            raise MissingRouteError(f'Cannot update route "{route_id}". Route doesn\'t exist.')
        return route_object

    def match(self, incoming_request: IncomingRequest) -> Optional[Route]:
        """Find matching Route and return apropriet RouteResponse or None."""
        for route in self.routes:
            if route.match(incoming_request):
                return route
        return None
