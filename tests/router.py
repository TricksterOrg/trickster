import http

import pytest
from fastapi import Request

from trickster.router import ParametrizedPath, Response, Router, Route

from typing import cast


class TestParametrizedPath:
    @pytest.mark.parametrize('raw, normalized', [
        ('/test', '/test'),
        ('test', '/test'),
        ('test/', '/test/'),
        ('/test/', '/test/'),
    ])
    def test_normalize_path(self, raw, normalized):
        assert ParametrizedPath._normalize(raw) == normalized

    @pytest.mark.parametrize('raw, normalized', [
        ('/test', '/test'),
        ('test', '/test'),
        ('test/', '/test/'),
        ('/test/', '/test/'),
    ])
    def test_validate(self, raw, normalized):
        path = ParametrizedPath.model_validate(raw)
        assert isinstance(path, ParametrizedPath)
        assert str(path) == normalized

    @pytest.mark.parametrize('parametrized, from_request, result', [
        ('/test', 'test', {}),
        ('test', 'test', {}),
        ('test/', 'test/', {}),
        ('/test/', 'test/', {}),
        ('/something', 'else/', None),
    ])
    def test_match(self, parametrized, from_request, result):
        path = ParametrizedPath.model_validate(parametrized)
        assert path.match_path(from_request) == result


class TestResponse:
    def test_get_fastapi_response(self):
        response = Response(
            status_code=http.HTTPStatus.OK,
            body={
                'foo': 'bar'
            },
            headers={
                'header': 'value'
            }
        ).as_fastapi_response()

        assert response.body == b'{"foo":"bar"}'
        assert response.status_code == 200
        assert response.headers.raw == [
            (b'header', b'value'),
            (b'content-length', b'13'),
            (b'content-type', b'application/json')
        ]


class MockedRequest:
    def __init__(self, method: str, path_params: dict[str, str]) -> None:
        self.method = method
        self.path_params = path_params


class TestRoute:
    def test_match_method(self):
        route = Route(path='test', responses=[], http_methods=[http.HTTPMethod.GET])
        assert route.match_method('GET') == http.HTTPMethod.GET

    def test_match_method_from_multiple(self):
        route = Route(path='test', responses=[], http_methods=[http.HTTPMethod.GET, http.HTTPMethod.POST])
        assert route.match_method('POST') == http.HTTPMethod.POST

    def test_match_method_with_no_match(self):
        route = Route(path='test', responses=[], http_methods=[http.HTTPMethod.GET])
        assert route.match_method('POST') is None


class TestRouter:
    def test_match(self):
        route = Route(path='/test', responses=[], http_methods=[http.HTTPMethod.GET])
        mocked_request = cast(Request, MockedRequest('GET', {'path': 'test'}))
        router = Router(routes=[route])
        match = router.match(mocked_request)

        assert match.route is route
        assert match.path_params == {}
        assert match.http_method == http.HTTPMethod.GET
