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
    context = ResponseContext()
    if route := current_app.user_router.match(incomming_request):
        context['route'] = route
        try:
            route.authenticate(incomming_request)
            response = route.select_response()
            context['response'] = response
        except AuthenticationError as error:
            response = route.auth.unauthorized_response
            context['error'] = error
        route.use(response)
        response.wait()
        return response.as_flask_response(context)
    abort(404)
