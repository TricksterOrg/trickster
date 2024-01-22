"""Endpoints mocking client service."""

import http

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from trickster.router import Router, get_router
from trickster.exceptions import ResourceNotFoundError, AuthenticationError


router = APIRouter(
    tags=['mocked'],
    include_in_schema=False
)


@router.api_route('/{path:path}', methods=http.HTTPMethod)  # type: ignore
def mocked_response(request: Request, mocked_router: Router = Depends(get_router)) -> JSONResponse:
    """All-catching route that mocks client service."""
    response = None

    if match := mocked_router.match(request):  # noqa: SIM102 - nested if statements
        match.route.hits += 1
        try:
            match.route.authenticate(request)
            if matched_response := match.route.get_response(match):
                response = matched_response
        except AuthenticationError:
            response = getattr(match.route.auth, 'error_response', None) or \
                mocked_router.get_error_response(status_code=http.HTTPStatus.UNAUTHORIZED)
    elif error_response := mocked_router.get_error_response(status_code=http.HTTPStatus.NOT_FOUND):
        response = error_response

    if response is not None:
        response.hits += 1
        response.delay_response()
        return response.as_fastapi_response()
    else:
        raise ResourceNotFoundError('No route or response was found for your request.')
