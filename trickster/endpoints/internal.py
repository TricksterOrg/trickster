"""Internal API endpoints."""

from __future__ import annotations

from flask import Blueprint, Response, abort, current_app, jsonify, make_response, request

from trickster.routing import RouteConfigurationError
from trickster.routing.input import IncomingTestRequest
from trickster.validation import request_schema


endpoints = Blueprint('internal_api', __name__)


@endpoints.route('/reset', methods=['POST'])
def reset() -> Response:
    """Reset Routes to default."""
    current_app.load_routes()  # type: ignore
    return make_response('', 204)


@endpoints.route('/routes', methods=['GET'])
def get_all_routes() -> Response:
    """Get list of configured Routes."""
    return jsonify(current_app.user_router.routes.serialize())  # type: ignore


@endpoints.route('/routes', methods=['POST'])
@request_schema('route.schema.json')
def add_route() -> Response:
    """Create new route."""
    try:
        route = current_app.user_router.add_route(request.get_json())  # type: ignore
        return make_response(jsonify(route.serialize()), 201)
    except RouteConfigurationError as error:
        abort(error.http_code, str(error))


@endpoints.route('/routes', methods=['DELETE'])
def remove_all_routes() -> Response:
    """Reset router configuration."""
    current_app.user_router.reset()  # type: ignore
    return make_response('', 204)


@endpoints.route('/routes/<string:route_id>', methods=['GET'])
def get_route(route_id: str) -> Response:
    """Get route by id."""
    if route := current_app.user_router.get_route(route_id):  # type: ignore
        return make_response(jsonify(route.serialize()), 200)
    abort(404, f'Route id "{route_id}" does not exist.')


@endpoints.route('/routes/<string:route_id>', methods=['PUT'])
@request_schema('route.schema.json')
def replace_route(route_id: str) -> Response:
    """Replace route with new data."""
    try:
        route = current_app.user_router.update_route(request.get_json(), route_id)  # type: ignore
        return make_response(jsonify(route.serialize()), 201)
    except RouteConfigurationError as error:
        abort(error.http_code, str(error))


@endpoints.route('/routes/<string:route_id>', methods=['DELETE'])
def remove_route(route_id: str) -> Response:
    """Remove route by id."""
    if current_app.user_router.get_route(route_id):  # type: ignore
        current_app.user_router.remove_route(route_id)  # type: ignore
        return make_response('', 204)
    abort(404, f'Route id "{route_id}" does not exist.')


@endpoints.route('/match_route', methods=['POST'])
@request_schema('request.schema.json')
def match_route() -> Response:
    """Match configured routes against given request."""
    payload = request.get_json()
    incoming_request = IncomingTestRequest(
        base_url=request.host_url,
        full_path=payload['path'],
        method=payload['method']
    )

    if route := current_app.user_router.match(incoming_request):  # type: ignore
        return make_response(jsonify(route.serialize()), 200)
    abort(404, 'No route was matched.')


@endpoints.route('/routes/<string:route_id>/responses', methods=['GET'])
def get_all_responses(route_id: str) -> Response:
    """Get all responses from given route."""
    if route := current_app.user_router.get_route(route_id):  # type: ignore
        return make_response(jsonify(route.responses.serialize()), 200)
    abort(404, f'Route id "{route_id}" does not exist.')


@endpoints.route('/routes/<string:route_id>/responses/<string:response_id>', methods=['GET'])
def get_response(route_id: str, response_id: str) -> Response:
    """Get response by id from given route.."""
    if route := current_app.user_router.get_route(route_id):  # type: ignore
        if response := route.get_response(response_id):
            return make_response(jsonify(response.serialize()), 200)
        abort(404, f'Response id "{response_id}" does not exist in request id "{route_id}".')
    abort(404, f'Route id "{route_id}" does not exist.')
