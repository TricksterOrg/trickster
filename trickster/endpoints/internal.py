"""Internal endpoints used to manipulate Trickster."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from trickster.schemas import HealthcheckStatus, InputRoute, InputResponse, InputResponseValidator
from trickster.router import Router, Route, get_router, Response, ResponseValidator


router = APIRouter(
    tags=['internal'],
    responses={
        404: {'description': 'Not found'}
    }
)


@router.get('/healthcheck')
def healthcheck() -> HealthcheckStatus:
    """Get info about Trickster health."""
    return HealthcheckStatus()


@router.get('/routes')
def get_routes(mocked_router: Router = Depends(get_router)) -> list[Route]:
    """Get list of all configured routes."""
    return mocked_router.routes


@router.get('/routes/{route_id}')
def get_route(route_id: uuid.UUID, mocked_router: Router = Depends(get_router)) -> Route:
    """Get route by its ID."""
    if route := mocked_router.get_route_by_id(route_id):
        return route
    raise HTTPException(status_code=404, detail=f'Route ID "{route_id}" was not found.')


@router.post('/routes')
def create_route(route: InputRoute, mocked_router: Router = Depends(get_router)) -> Route:
    """Create new route."""
    try:
        new_route = Route(**route.model_dump())
        new_route.validate_existing_response_validator_combinations()
        mocked_router.routes.append(new_route)
        return new_route
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f'Failed validation: {e}') from e


@router.delete('/routes')
def delete_routes(mocked_router: Router = Depends(get_router)) -> list[Route]:
    """Remove all configured routes.

    Removes also routes created from an openapi specification on startup.
    """
    mocked_router.routes = []
    return mocked_router.routes


@router.delete('/routes/{route_id}')
def delete_route(route_id: uuid.UUID, mocked_router: Router = Depends(get_router)) -> list[Route]:
    """Remove route by ID."""
    if route := mocked_router.get_route_by_id(route_id):
        mocked_router.routes.remove(route)
        return mocked_router.routes
    raise HTTPException(status_code=404, detail=f'Route "{route_id}" was not found.')


@router.get('/routes/{route_id}/responses')
def get_route_responses(route_id: uuid.UUID, mocked_router: Router = Depends(get_router)) -> list[Response]:
    """Get list of all responses configured for a route."""
    if route := mocked_router.get_route_by_id(route_id):
        return route.responses
    raise HTTPException(status_code=404, detail=f'Route "{route_id}" was not found.')


@router.delete('/routes/{route_id}/responses/{response_id}')
def delete_route_response(
    route_id: uuid.UUID, response_id: uuid.UUID, mocked_router: Router = Depends(get_router)
) -> Route:
    """Delete a route response."""
    if route := mocked_router.get_route_by_id(route_id):
        if response := route.get_response_by_id(response_id):
            route.responses.remove(response)
            return route
        raise HTTPException(status_code=404, detail=f'Response "{response_id}" was not found in route "{route_id}".')
    raise HTTPException(status_code=404, detail=f'Route "{route_id}" was not found.')


@router.delete('/routes/{route_id}/responses')
def delete_route_responses(route_id: uuid.UUID, mocked_router: Router = Depends(get_router)) -> Route:
    """Delete all responses of a route."""
    if route := mocked_router.get_route_by_id(route_id):
        route.responses = []
        return route
    raise HTTPException(status_code=404, detail=f'Route "{route_id}" was not found.')


@router.post('/routes/{route_id}/responses')
def create_route_response(
    route_id: uuid.UUID, response: InputResponse, mocked_router: Router = Depends(get_router)
) -> Route:
    """Create new response for a route."""
    if route := mocked_router.get_route_by_id(route_id):
        try:
            new_response = Response(**response.model_dump())
            route.validate_new_response(new_response)
            route.responses.append(new_response)
            return route
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f'Failed validation: {e}') from e
    raise HTTPException(status_code=404, detail=f'Route "{route_id}" was not found.')


@router.get('/routes/{route_id}/response_validators')
def get_route_response_validators(
    route_id: uuid.UUID, mocked_router: Router = Depends(get_router)
) -> list[ResponseValidator]:
    """Get validators configured for a route responses."""
    if route := mocked_router.get_route_by_id(route_id):
        return route.response_validators
    raise HTTPException(status_code=404, detail=f'Route "{route_id}" was not found.')


@router.delete('/routes/{route_id}/response_validators/{validator_id}')
def delete_route_response_validator(
    route_id: uuid.UUID, validator_id: uuid.UUID, mocked_router: Router = Depends(get_router)
) -> Route:
    """Remove validator configured for a route responses."""
    if route := mocked_router.get_route_by_id(route_id):
        if validator := route.get_response_validator_by_id(validator_id):
            route.response_validators.remove(validator)
            try:
                route.validate_existing_response_validator_combinations()
            except ValidationError as e:
                route.response_validators.append(validator)
                raise e
            return route
        raise HTTPException(
            status_code=404,
            detail=f'Response_validator "{validator_id}" was not found in route "{route_id}".'
        )
    raise HTTPException(status_code=404, detail=f'Route "{route_id}" was not found.')


@router.delete('/routes/{route_id}/response_validators')
def delete_route_response_validators(route_id: uuid.UUID, mocked_router: Router = Depends(get_router)) -> Route:
    """Remove all validators configured for a route responses."""
    if route := mocked_router.get_route_by_id(route_id):
        route.response_validators = []
        return route
    raise HTTPException(status_code=404, detail=f'Route "{route_id}" was not found.')


@router.post('/routes/{route_id}/response_validators')
def create_route_response_validator(
    route_id: uuid.UUID, validator: InputResponseValidator, mocked_router: Router = Depends(get_router)
) -> Route:
    """Create new validator for route responses."""
    if route := mocked_router.get_route_by_id(route_id):
        try:
            new_validator = ResponseValidator(**validator.model_dump())
            route.validate_new_response_validator(new_validator)
            route.response_validators.append(new_validator)
            return route
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f'Failed validation: {e}') from e
    raise HTTPException(status_code=404, detail=f'Route "{route_id}" was not found.')
