"""API endpoints."""

from __future__ import annotations

from flask import Blueprint, Response, request, current_app, jsonify, abort

from trickster.router import RouteConfigurationError
from trickster.input import IncommingTestRequest, IncommingFlaskRequest, HTTP_METHODS
from trickster.validation import request_schema
from trickster.auth import AuthenticationError


internal_api = Blueprint('internal_api', __name__)
external_api = Blueprint('external_api', __name__)


@internal_api.route('/routes', methods=['DELETE'])
def reset_router() -> Response:
    """Reset router configuration."""
    current_app.user_router.reset()
    return Response(response='', status=200)


@internal_api.route('/route', methods=['POST'])
@request_schema('route.schema.json')
def add_route() -> Response:
    """Create new route."""
    try:
        route = current_app.user_router.add_route(request.get_json())
        return jsonify(route.serialize())
    except RouteConfigurationError as error:
        abort(400, str(error))


@internal_api.route('/routes', methods=['POST'])
@request_schema('routes.schema.json')
def add_routes() -> Response:
    """Create multiple new routes."""
    try:
        routes = current_app.user_router.add_routes(request.get_json())
        return jsonify([route.serialize() for route in routes])
    except RouteConfigurationError as error:
        abort(400, str(error))


@internal_api.route('/routes', methods=['GET'])
def get_all_routes() -> Response:
    """Get list of configured routes and responses."""
    return jsonify(current_app.user_router.serialize())


@internal_api.route('/route/<string:route_id>', methods=['GET'])
def get_route(route_id: str) -> Response:
    """Get single route by id."""
    if route := current_app.user_router.get_route(route_id):
        return jsonify(route.serialize())
    abort(404, f'Route id "{route_id}" does not exist.')


@internal_api.route('/routes/match', methods=['POST'])
@request_schema('match_route.schema.json')
def match_route() -> Response:
    """Match configured routes against given request."""
    payload = request.get_json()
    incomming_request = IncommingTestRequest(
        base_url=request.host_url,
        full_path=payload['path'],
        method=payload['method']
    )

    if route := current_app.user_router.match(incomming_request):
        return jsonify(route.serialize())
    abort(404, 'No route was matched.')


@internal_api.route('/route/<string:route_id>/response/<string:response_id>', methods=['GET'])
def get_response(route_id: str, response_id: str) -> Response:
    """Reset router configuration."""
    if route := current_app.user_router.get_route(route_id):
        if response := route.get_response(response_id):
            return jsonify(response.serialize())
        abort(404, f'Response id "{response_id}" does not exist in request id "{route_id}".')
    abort(404, f'Route id "{route_id}" does not exist.')


@external_api.route('/<path:path>', methods=HTTP_METHODS)
def respond(path: str) -> Response:
    """Match request againts defined routes and return appropriet response."""
    try:
        if route := current_app.user_router.match(IncommingFlaskRequest(request)):
            if response := route.select_response():
                response.wait()
                route.use(response)
                return response.as_flask_response()
        abort(404)
    except AuthenticationError as error:
        abort(401, str(error))
