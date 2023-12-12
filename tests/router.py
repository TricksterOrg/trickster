import http
import uuid

from fastapi import Request

from trickster.model import Route, Response
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

    def test_get_route_by_id(self):
        route_id = uuid.uuid4()
        routes = [
            Route(id=route_id, path='/test', responses=self.responses, http_methods=[http.HTTPMethod.GET]),
            Route(path='/test', responses=self.responses, http_methods=[http.HTTPMethod.GET]),
        ]
        router = Router(routes=[])

        assert router.get_route_by_id(route_id) is None
        assert Router(routes=routes).get_route_by_id(route_id) == routes[0]
