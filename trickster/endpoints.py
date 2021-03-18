"""API endpoints."""

from __future__ import annotations

from flask import Blueprint, Response, request, current_app, jsonify, abort, make_response

from trickster import RouteConfigurationError
from trickster.input import IncommingTestRequest, IncommingFlaskRequest, HTTP_METHODS
from trickster.validation import request_schema
from trickster.auth import AuthenticationError


internal_api = Blueprint('internal_api', __name__)
external_api = Blueprint('external_api', __name__)


@internal_api.route('/routes', methods=['GET'])
def get_all_routes() -> Response:
    """Get list of configured routes and responses."""
    return jsonify(current_app.user_router.serialize())


@internal_api.route('/routes', methods=['POST'])
@request_schema('route.schema.json')
def add_route() -> Response:
    """Create new route."""
    try:
        route = current_app.user_router.add_route(request.get_json())
        return make_response(jsonify(route.serialize()), 201)
    except RouteConfigurationError as error:
        abort(error.http_code, str(error))


@internal_api.route('/routes', methods=['DELETE'])
def remove_all_routes() -> Response:
    """Reset router configuration."""
    current_app.user_router.reset()
    return make_response('', 204)


@internal_api.route('/routes/<string:route_id>', methods=['GET'])
def get_route(route_id: str) -> Response:
    """Get route by id."""
    if route := current_app.user_router.get_route(route_id):
        return make_response(jsonify(route.serialize()), 200)
    abort(404, f'Route id "{route_id}" does not exist.')


@internal_api.route('/routes/<string:route_id>', methods=['PUT'])
@request_schema('route.schema.json')
def replace_route(route_id: str) -> Response:
    """Replace route with new data."""
    try:
        route = current_app.user_router.update_route(request.get_json(), route_id)
        return make_response(jsonify(route.serialize()), 201)
    except RouteConfigurationError as error:
        abort(error.http_code, str(error))


@internal_api.route('/routes/<string:route_id>', methods=['DELETE'])
def remove_route(route_id: str) -> Response:
    """Remove route by id."""
    if current_app.user_router.get_route(route_id):
        current_app.user_router.remove_route(route_id)
        return make_response('', 204)
    abort(404, f'Route id "{route_id}" does not exist.')


@internal_api.route('/match_route', methods=['POST'])
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
        return make_response(jsonify(route.serialize()), 200)
    abort(404, 'No route was matched.')


@internal_api.route('/routes/<string:route_id>/responses/<string:response_id>', methods=['GET'])
def get_response(route_id: str, response_id: str) -> Response:
    """Reset router configuration."""
    if route := current_app.user_router.get_route(route_id):
        if response := route.get_response(response_id):
            return make_response(jsonify(response.serialize()), 200)
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
