"""Internal router used to match client defined routes."""

from __future__ import annotations

import enum
import http
import functools
import uuid
import re
import random
import time

import jsonschema
from typing_extensions import Annotated
from pydantic import BaseModel, Field, model_serializer, model_validator
from fastapi import Request
from fastapi.responses import JSONResponse

from typing import Any


HitCounter = Annotated[int, Field(gte=0, default=0, description='Number of times route or response was used')]
JsonBody = Annotated[dict | list, Field(description='Request or response body as a json')]
PathParams = Annotated[dict[str, Any], Field(description='Parameter parsed from a route path')]


class ParametrizedPath(BaseModel):
    """URL path that can match path of mocked request.

    Path is a normal url path without domain and port, e.g. `/api/v1/endpoint`. `/` at the beginning will be added
    automatically if omitted.

    Parts of the url path can be replaced with placeholders. Route will then match any path as long as the rest of
    the path matches and the variable is of specified type. E.g. `/api/v{version:int}/endpoint` will match any
    version of the endpoint - `/api/v1/endpoint`, `/api/v1234/endpoint` etc. Name of the variable (`version` from
    above example) is not important as long as it's unique within the path.

    Available types are:
    - `integer`: any natural number
    - `number`: sequence of digits with optional `,` or `.`
    - `string`: any string without `/` and `?`
    - `boolean`: `0` or `1`
    - `uuid4`: string in UUID4 format
    """

    _VARIABLE_TYPE_PATTERNS = {
        'integer': r'[1-9]\d*',
        'number': r'\d+(?:[\.,]\d+)?',
        'string': r'[^\\/\s?]+',
        'boolean': r'[01]',
        'uuid4': r'[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}',
    }  # Mapping of path variable type to regex

    path: str = Field(description='Raw path provided by the user')

    @model_serializer
    def serialize_model(self) -> str:
        """Serialize model for purposes of Pydantic."""
        return str(self)

    @model_validator(mode='before')
    @classmethod
    def validate_model(cls, value: str) -> dict[str, str]:
        """Validate model and provided path."""
        if not isinstance(value, str):
            raise ValueError(f'MatchablePath: string expected not {type(value)}')
        value = cls._normalize(value)
        return {'path': value}

    @classmethod
    def _normalize(cls, value: str) -> str:
        """Normalize path.

        Convert path to normal form - starting with /.
        """
        if not value.startswith('/'):
            value = f'/{value}'
        return value

    @functools.cached_property
    def variables_regex(self) -> re.Pattern:
        """Regex that can find variables configured in a path."""
        types_pattern = '|'.join(self._VARIABLE_TYPE_PATTERNS.keys())
        return re.compile(rf'(?P<placeholder>{{(?P<name>\w+):(?P<type>{types_pattern})}})')

    @functools.cached_property
    def path_regex(self) -> re.Pattern:
        """Regular expression that can match and parse-out variables from a path."""
        path_pattern = re.escape(self.path)  # escape special characters
        path_pattern = path_pattern.replace(r'\{', '{').replace(r'\}', '}')  # unescape { and }
        path_pattern = f'^{path_pattern}$'  # match from start to end

        for match in self.variables_regex.finditer(self.path):
            variable = match.groupdict()
            type_pattern = self._VARIABLE_TYPE_PATTERNS[variable['type']]
            variable_regex = rf'(?P<{variable["name"]}>{type_pattern})'
            path_pattern = path_pattern.replace(variable['placeholder'], variable_regex)

        return re.compile(path_pattern)

    def match_path(self, path: str) -> dict[str, Any] | None:
        """Return matched URL params if this path matches given path."""
        if match := self.path_regex.match(self._normalize(path)):
            return match.groupdict()
        return None

    def __str__(self) -> str:
        """Get string representation of the path."""
        return self.path


class ResponseValidator(BaseModel):
    """Validator of responses.

    Validators can be added to a Route to make sure all configured responses match a given json schema. They affect
    only adding responses using the internal endpoints. They don't affect how the mocked routes behave.

    Each route much be valid in at least one validator, unless there are no validators configured.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, description='Unique identifier')  # noqa: A003
    status_code: http.HTTPStatus = Field(description='Status code as integer')
    json_schema: dict[str, Any] = Field(description='Json schema')

    def validate_response(self, response: Response) -> None:
        """Validate response against json schema."""
        if response.status_code != self.status_code:
            raise ValueError('Route response validation failed.')
        try:
            jsonschema.validate(response.body, self.json_schema)
        except jsonschema.exceptions.ValidationError:
            raise ValueError('JsonSchema validation failed.')


class RouteMatch(BaseModel):
    """Information from a route matching process."""

    route: Route = Field(description='Matched route')
    http_method: http.HTTPMethod = Field(description='Matched http method')
    path_params: PathParams = Field(description='Matched path parameters')


class ResponseDelay(BaseModel):
    """Delay of a route response.

    Delay can be provided either as a single number which will result in every response being delayed but exactly that
    amount of time. Or as a list containing two numbers in which case the response will be delayed by random number of
    seconds between these two numbers.
    """

    min_delay: float = Field(ge=0, default=0.0, description='Minimum delay')
    max_delay: float = Field(ge=0, default=0.0, description='Maximum delay')

    @model_serializer
    def serialize_model(self) -> tuple[float, float]:
        """Serialize model for purposes of Pydantic."""
        return self.min_delay, self.max_delay

    @model_validator(mode='before')
    @classmethod
    def validate_model(cls, data: dict[str, float] | float | list[float] | tuple[float, float]) -> dict[str, Any]:
        """Validate provided data and convert them to two numbers if only one is provided."""
        if isinstance(data, dict):
            min_delay = data.get('min_delay', 0.0)
            max_delay = max(data.get('max_delay', 0.0), min_delay)
        elif isinstance(data, (int, float)):
            min_delay = float(data)
            max_delay = float(data)
        elif isinstance(data, (list, tuple)) and len(data) == 2:
            min_delay = float(data[0])
            max_delay = float(data[1])
        else:
            raise ValueError('Input of response delay must be a single value or list of two numbers.')

        if min_delay > max_delay:
            raise ValueError(f'Maximum delay ({max_delay}s) must be greater than minimum delay ({min_delay}s).')

        return {
            'min_delay': min_delay,
            'max_delay': max_delay
        }

    def delay_response(self) -> None:
        """Pause the program for specified time."""
        time.sleep(random.uniform(self.min_delay, self.max_delay))


class Response(BaseModel):
    """User-defined response Trickster should return when a request matches a response."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, description='Unique identifier')  # noqa: A003
    hits: HitCounter

    status_code: http.HTTPStatus = Field(description='Status code of the response as int')
    body: JsonBody
    delay: ResponseDelay = ResponseDelay()
    headers: dict[str, str] = Field(default_factory=dict, description='Header of the response')
    weight: float = Field(ge=0.0, default=1.0, description='Weight of the response when selecting random response')

    def as_fastapi_response(self) -> JSONResponse:
        """Create a response that can be returned by FastApi."""
        return JSONResponse(
            content=self.body,
            status_code=self.status_code,
            headers=self.headers
        )

    def delay_response(self) -> None:
        """Stop program for a specified amount of time."""
        self.delay.delay_response()


class ResponseSelector(enum.Enum):
    """Algorithm to select response from matched route.

    - `RANDOM`: Select response by random from all available
    - `FIRST`: Select first response from all available
    - `BALANCED`: Select response that was returned the least
    """

    RANDOM = 'random'
    FIRST = 'first'
    BALANCED = 'balanced'

    def select_response(self, responses: list[Response]) -> Response:
        """Select response based on response selector."""
        if not responses:
            raise ValueError('No suitable response found.')

        match self:
            case ResponseSelector.FIRST:
                return responses[0]
            case ResponseSelector.RANDOM:
                weights = [response.weight for response in responses]
                return random.choices(responses, weights=weights, k=1)[0]
            case ResponseSelector.BALANCED:
                return min(responses, key=lambda response: response.hits)
            case _:
                raise ValueError(f'Response selection algorithm for {self.value} is not configured.')


class Route(BaseModel):
    """User-defined route that can match request and return a response."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, description='Unique identifier')  # noqa: A003
    hits: HitCounter = 0

    path: ParametrizedPath
    http_methods: list[http.HTTPMethod] = Field(default=[http.HTTPMethod.GET], description='Method the route matches')
    response_validators: list[ResponseValidator] = Field(default_factory=list, description='Response validators')
    responses: list[Response] = Field(default_factory=list, description='Possible responses of the route')
    response_selector: ResponseSelector = Field(
        default=ResponseSelector.RANDOM, description='Strategy for response selection')

    @model_validator(mode='after')  # type: ignore # github.com/python/mypy/issues/15620
    @classmethod
    def validate_model(cls, route: Route) -> Route:
        """Validate that all combinations of responses and their validators are valid."""
        for response in route.responses:
            route.validate_new_response(response)
        return route

    def validate_existing_response_validator_combinations(self):
        """Validate that all combinations of responses and their validators are valid."""
        for response in self.responses:
            self.validate_new_response(response)

    def validate_new_response_validator(self, validator: ResponseValidator):
        """Validate that new response validator can be safely added."""
        if not self.response_validators:
            # Don't need to validate if there already are some validators as new one just adds more options
            for response in self.responses:
                validator.validate_response(response)

    def validate_new_response(self, response: Response) -> None:
        """Validate that response matches at least one configured validator and can be added."""
        if not self.response_validators:
            return

        for validator in self.response_validators:
            try:
                validator.validate_response(response)
            except ValueError:
                continue  # Didn't pass this one, continue to next one
            else:
                return
        raise ValueError(f'Response "{response.id}" doesn\'t match ony of the configured validators.')

    def match(self, request: Request) -> tuple[http.HTTPMethod, PathParams] | None:
        """If route matches a request, return http method and path params."""
        http_method = self.match_method(http.HTTPMethod(request.method))
        if http_method is not None:
            path_params = self.path.match_path(request.path_params['path'])
            if path_params is not None:
                return http_method, path_params
        return None

    def match_method(self, method: http.HTTPMethod) -> http.HTTPMethod | None:
        """Return http method if it matched configured method for this route."""
        if method in self.http_methods:
            return method
        return None

    def get_response(self, match: RouteMatch) -> Response:
        """Get a response of this route."""
        response = self.response_selector.select_response(self.responses)
        return response

    def get_response_by_id(self, response_id: uuid.UUID) -> Response | None:
        """Get response by ID."""
        for response in self.responses:
            if response.id == response_id:
                return response
        return None

    def get_response_validator_by_id(self, validator_id: uuid.UUID) -> ResponseValidator | None:
        """Get response validator by ID."""
        for validator in self.response_validators:
            if validator.id == validator_id:
                return validator
        return None


class Router(BaseModel):
    """Router containing routes that can match user request."""

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

    def get_route_by_id(self, route_id: uuid.UUID) -> Route | None:
        """Get route by id."""
        for route in self.routes:
            if route.id == route_id:
                return route
        return None


@functools.cache
def get_router() -> Router:
    """Get a router."""
    return Router()
