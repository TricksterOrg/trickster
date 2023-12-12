import http

import pytest

from trickster.model import ParametrizedPath, Response, Route, TokenAuth


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

    @pytest.mark.parametrize('body, auth_model', [
        ({
            "path": "/test1",
            "responses": [
                {
                    "status_code": 200,
                    "body": {"test": "test"}
                }
            ],
            "auth": {
                "method": "token",
                "token": "testtoken",
                "error_response": {
                    "status_code": 400,
                    "body": {"auth": "unauthorized"}
                }
            }
        }, TokenAuth)
    ])
    def test_create_proper_auth(self, body, auth_model):
        """Test route will create proper auth method."""
        route = Route.model_validate(body)
        assert isinstance(route.auth, auth_model)