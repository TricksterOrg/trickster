"""Pydantic schemas that don't fit anywhere else."""

import http

from pydantic import BaseModel, Field

from trickster.router import ParametrizedPath, JsonBody, ResponseValidator, ResponseSelector, ResponseDelay

from typing import Literal, Any


class HealthcheckStatus(BaseModel):
    """Healthcheck endpoint response schema."""

    status: Literal['OK'] = 'OK'


class InputResponseValidator(BaseModel):
    """Validator of responses.

    Validators can be added to a Route to make sure all configured responses match a given json schema. They affect
    only adding responses using the internal endpoints. They don't affect how the mocked routes behave.

    Each validator is set to validate only responses with given status code, other status codes are ignored.

    If there are multiple validators configured for a response, the response must be valid in at least one of them.
    """

    status_code: http.HTTPStatus
    json_schema: dict[str, Any]


class InputResponse(BaseModel):
    """User-defined response Trickster should return when a request matches a response."""

    status_code: http.HTTPStatus
    body: JsonBody
    delay: ResponseDelay = Field(default_factory=ResponseDelay)
    headers: dict[str, str] = {}
    weight: float = Field(ge=0.0, default=1.0)


class InputRoute(BaseModel):
    """User-defined route that can match request and return a response."""

    path: ParametrizedPath
    responses: list[InputResponse] = []
    http_methods: list[http.HTTPMethod] = [http.HTTPMethod.GET]
    response_validators: list[ResponseValidator] = []
    response_selector: ResponseSelector = ResponseSelector.RANDOM
