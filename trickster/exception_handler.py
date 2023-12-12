"""Handlers for HTTP errors."""
import functools

import fastapi
import jsonschema

from typing import Any, Callable, Coroutine

from trickster.exceptions import ValidationError, AuthenticationError, ResourceNotFoundError


async def handle_general_json_error(
    request: fastapi.Request,
    exception: Exception,
    reason: str,
    status_code: int,
) -> fastapi.responses.Response:
    """Return error response."""
    return fastapi.responses.JSONResponse(
        {
            'error': reason,
            'reason': str(exception)
        },
        status_code=status_code
    )


handle_validation_error = functools.partial(
    handle_general_json_error,
    reason='Validation error',
    status_code=fastapi.status.HTTP_400_BAD_REQUEST
)
handle_authentication_error = functools.partial(
    handle_general_json_error,
    reason='Authentication error',
    status_code=fastapi.status.HTTP_401_UNAUTHORIZED
)
handle_resource_not_found_error = functools.partial(
    handle_general_json_error,
    reason='Resource error',
    status_code=fastapi.status.HTTP_404_NOT_FOUND
)

request_error_handlers: dict[
    int | type[Exception],
    Callable[[fastapi.Request, Any], Coroutine[Any, Any, fastapi.responses.Response]]
] = {
    ValidationError: handle_validation_error,
    AuthenticationError: handle_authentication_error,
    ResourceNotFoundError: handle_resource_not_found_error,
    fastapi.exceptions.RequestValidationError: handle_validation_error,
    fastapi.exceptions.ResponseValidationError: handle_validation_error,
    fastapi.exceptions.ValidationException: handle_validation_error,
    ValueError: handle_validation_error,
    jsonschema.exceptions.ValidationError: handle_validation_error,
}
