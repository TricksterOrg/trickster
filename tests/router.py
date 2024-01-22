import http
import uuid

from fastapi import Request

from trickster.model import Route, Response, ResponseSelector
from trickster.router import Router

from typing import cast


class MockedRequest:
    def __init__(self, method: str, path_params: dict[str, str]) -> None:
        self.method = method
        self.path_params = path_params


class TestRouter:
    responses = [
        Response(status_code=http.HTTPStatus.OK, body={'body': 1}, hits=3),
        Response(status_code=http.HTTPStatus.OK, body={'body': 'two'}, hits=2),
        Response(id=uuid.uuid4(), status_code=http.HTTPStatus.OK, body={'body': 3}, hits=1),
        Response(status_code=http.HTTPStatus.OK, body={'body': 4}, hits=0),
        Response(status_code=http.HTTPStatus.OK, body={'body': 5}, hits=4),
    ]

    error_responses = [
        Response(status_code=http.HTTPStatus.NOT_FOUND, body={'body': 1}, hits=3),
        Response(status_code=http.HTTPStatus.BAD_REQUEST, body={'body': 'two'}, hits=2),
        Response(status_code=http.HTTPStatus.BAD_REQUEST, body={'body': 'three'}, hits=2),
    ]

    routes = [
        Route(path='/test', responses=responses, http_methods=[http.HTTPMethod.GET]),
        Route(path='/mest', responses=responses, http_methods=[http.HTTPMethod.GET]),
    ]

    def test_match(self):
        route = Route(path='/test', responses=[], http_methods=[http.HTTPMethod.GET])
        mocked_request = cast(Request, MockedRequest('GET', {'path': 'test'}))
        router = Router(routes=[route])
        match = router.match(mocked_request)

        assert match.route is route
        assert match.path_params == {}
        assert match.http_method == http.HTTPMethod.GET

        router = Router(routes=[])
        assert router.match(mocked_request) is None

    def test_get_routes(self):
        assert Router(routes=self.routes).get_routes() == self.routes

    def test_add_routes(self):
        router = Router(routes=[])
        route = Route(path='/test', responses=[], http_methods=[http.HTTPMethod.GET])

        router.add_route(route)

        assert router.routes[0] == route

    def test_delete_route(self):
        router = Router(routes=self.routes)

        router.delete_route(self.routes[0])

        assert self.routes[0] not in router.routes

    def test_delete_routes(self):
        router = Router(routes=self.routes)

        router.delete_routes()

        assert len(router.routes) == 0

    def test_get_route_by_id(self):
        route_id = uuid.uuid4()
        routes = [
            Route(id=route_id, path='/test', responses=self.responses, http_methods=[http.HTTPMethod.GET]),
            Route(path='/test', responses=self.responses, http_methods=[http.HTTPMethod.GET]),
        ]

        assert Router(routes=[]).get_route_by_id(route_id) is None
        assert Router(routes=routes).get_route_by_id(uuid.uuid4()) is None
        assert Router(routes=routes).get_route_by_id(route_id) == routes[0]

    def test_get_error_response(self):
        router = Router(
            routes=self.routes, error_responses=self.error_responses,
            error_response_selector=ResponseSelector.FIRST
        )

        assert router.get_error_response(http.HTTPStatus.NOT_FOUND) == self.error_responses[0]
        assert Router(routes=self.routes).get_error_response(http.HTTPStatus.NOT_FOUND) is None

    def test_get_error_responses(self):
        router = Router(routes=self.routes, error_responses=self.error_responses)

        assert router.get_error_responses() == self.error_responses
        assert router.get_error_responses(http.HTTPStatus.BAD_REQUEST) == self.error_responses[1:]

    def test_add_error_response(self):
        router = Router(routes=self.routes)

        router.add_error_response(self.error_responses[0])

        assert router.error_responses == [self.error_responses[0]]

        router.add_error_response(self.error_responses[1])

        assert router.error_responses == [self.error_responses[0], self.error_responses[1]]

    def test_get_error_response_by_id(self):
        error_response_id = uuid.uuid4()
        error_responses = [
            Response(id=error_response_id, status_code=http.HTTPStatus.NOT_FOUND, body={'body': 1}, hits=3),
            Response(status_code=http.HTTPStatus.BAD_REQUEST, body={'body': 'two'}, hits=2),
        ]

        router = Router(routes=self.routes, error_responses=error_responses)

        assert router.get_error_response_by_id(uuid.uuid4()) is None
        assert router.get_error_response_by_id(error_response_id) == error_responses[0]

    def test_delete_error_response(self):
        router = Router(routes=self.routes, error_responses=self.error_responses)

        router.delete_error_response(self.error_responses[0])

        assert router.error_responses == self.error_responses[1:]
