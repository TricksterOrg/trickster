"""Endpoints mocking client service."""

import http

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse

from trickster.router import Router, get_router


router = APIRouter(
    tags=['mocked'],
    include_in_schema=False
)


@router.api_route('/{path:path}', methods=http.HTTPMethod)  # type: ignore
def mocked_response(request: Request, mocked_router: Router = Depends(get_router)) -> JSONResponse:
    """All-catching route that mocks client service."""
    if match := mocked_router.match(request):  # noqa: SIM102 - nested if statements
        if response := match.route.get_response(match):
            match.route.hits += 1
            response.hits += 1
            response.delay_response()
            return response.as_fastapi_response()
    raise HTTPException(status_code=404, detail='No route or response was found for your request.')
