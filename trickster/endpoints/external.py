"""External API endpoints."""

from __future__ import annotations

from flask import Blueprint, Response, abort, current_app, request

from trickster.routing import ResponseContext
from trickster.routing.auth import AuthenticationError
from trickster.routing.input import HTTP_METHODS, IncomingFlaskRequest


endpoints = Blueprint('external_api', __name__)


@endpoints.route('/<path:path>', methods=HTTP_METHODS)
def respond(path: str) -> Response:
    """Match request againts defined routes and return appropriet response."""
    incomming_request = IncomingFlaskRequest(request)
    try:
        if route := current_app.user_router.match(incomming_request):
            route.authenticate(incomming_request)
            response = route.select_response()
            route.use(response)
            response.wait()
            context = ResponseContext({})
            return response.as_flask_response(context)
        abort(404)
    except AuthenticationError as error:
        abort(401, str(error))
