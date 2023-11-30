import http

from fastapi import Request

from trickster.model import Route
from trickster.router import Router

from typing import cast


class MockedRequest:
    def __init__(self, method: str, path_params: dict[str, str]) -> None:
        self.method = method
        self.path_params = path_params


class TestRouter:
    def test_match(self):
        route = Route(path='/test', responses=[], http_methods=[http.HTTPMethod.GET])
        mocked_request = cast(Request, MockedRequest('GET', {'path': 'test'}))
        router = Router(routes=[route])
        match = router.match(mocked_request)

        assert match.route is route
        assert match.path_params == {}
        assert match.http_method == http.HTTPMethod.GET
