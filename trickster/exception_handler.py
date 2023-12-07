"""Handlers for HTTP errors."""

import fastapi
import jsonschema

from typing import Any, Callable, Coroutine

from trickster.exceptions import ValidationError, AuthenticationError, ResourceNotFoundError


async def handle_validation_error(
    request: fastapi.Request, exception: Exception
) -> fastapi.responses.Response:
    """Handle validation error."""
    return fastapi.responses.JSONResponse(
        {
            'error': 'Validation error',
            'reason': str(exception)
        },
        status_code=fastapi.status.HTTP_400_BAD_REQUEST
    )


async def handle_authentication_error(
    request: fastapi.Request, exception: Exception
) -> fastapi.responses.Response:
    """Handle validation error."""
    return fastapi.responses.JSONResponse(
        {
            'error': 'Authentication error',
            'reason': str(exception)
        },
        status_code=fastapi.status.HTTP_401_UNAUTHORIZED
    )


async def handle_resource_not_found_error(
    request: fastapi.Request, exception: Exception
) -> fastapi.responses.Response:
    """Handle validation error."""
    return fastapi.responses.JSONResponse(
        {
            'error': 'Resource error',
            'reason': str(exception)
        },
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