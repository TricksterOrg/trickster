import http
import copy
import random
import uuid

import pytest
from fastapi import Request

from trickster.model import (
    ParametrizedPath, Response, Route, ResponseDelay, ResponseValidator, ResponseSelector,
    RouteMatch, InputResponseValidator, InputResponse, InputRoute, HealthcheckStatus
)

from typing import cast


class MockedRequest:
    def __init__(self, method: str, path_params: dict[str, str]) -> None:
        self.method = method
        self.path_params = path_params


class TestParametrizedPath:
    def test_serialize_model(self):
        path = ParametrizedPath.model_validate('users/{user_id:integer}/books')

        assert path.serialize_model() == '/users/{user_id:integer}/books'

    @pytest.mark.parametrize('raw, normalized', [
        ('/test', '/test'),
        ('test', '/test'),
        ('test/', '/test/'),
        ('/test/', '/test/'),
    ])
    def test_validate_model(self, raw, normalized):
        path = ParametrizedPath.model_validate(raw)

        assert isinstance(path, ParametrizedPath)
        assert str(path) == normalized

    @pytest.mark.parametrize(
        'data',
        [
            True,
            123,
            {},
            []
        ]
    )
    def test_validate_model_invalid(self, data):
        with pytest.raises(ValueError):
            ParametrizedPath.validate_model(data)

    @pytest.mark.parametrize('parametrized, from_request, result', [
        ('/test', 'test', {}),
        ('test', 'test', {}),
        ('test/', 'test/', {}),
        ('/test/', 'test/', {}),
        ('/something', 'else/', None),
        ('/users/d{somevar:wrongtype}/books', '/just/a/path', None),
        ('/users/{user_id:integer}/books', '/users/1234/books', {'user_id': '1234'}),
        ('/users/{user_id:number}/books', '/users/12.34/books', {'user_id': '12.34'}),
        ('/users/{user_id:string}/books', '/users/23ad3fa3@/books', {'user_id': '23ad3fa3@'}),
        ('/users/{user_id:boolean}/books', '/users/0/books', {'user_id': '0'}),
        ('/users/{user_id:uuid4}/books', '/users/9566b682-3531-49aa-ab11-724d3cb3b5fd/books',
         {'user_id': '9566b682-3531-49aa-ab11-724d3cb3b5fd'}
         ),
        ('/users/{user_id:integer}/books/{book_name:string}', '/users/1234/books/SomeBookName',
         {'user_id': '1234', 'book_name': 'SomeBookName'}
         ),
    ])
    def test_match_path(self, parametrized, from_request, result):
        path = ParametrizedPath.model_validate(parametrized)

        assert path.match_path(from_request) == result


class TestResponseValidator:
    def test_validate_response_valid(self):
        response = Response(status_code=http.HTTPStatus.OK, body={'some': 'body', 'extra': 1})
        response_validator = ResponseValidator(
            status_code=http.HTTPStatus.OK,
            json_schema={
                '$schema': 'https://json-schema.org/draft/2020-12/schema',
                'properties': {'some': {'type': 'string'}}
            },
        )

        assert response_validator.validate_response(response) is None

    @pytest.mark.parametrize(
        'data, expectation',
        [
            pytest.param(
                {'status_code': http.HTTPStatus.NOT_FOUND,
                 'json_schema': {'$schema': 'https://json-schema.org/draft/2020-12/schema'}
                 },
                f'{ValueError.__name__}: Route response validation failed.',
                id='Invalid HTTP status code'
            ),
            pytest.param(
                {'status_code': http.HTTPStatus.OK,
                 'json_schema': {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'number'}
                 },
                f'{ValueError.__name__}: JsonSchema validation failed.',
                id='Invalid response against JSON schema'
            )
        ]
    )
    def test_validate_response_invalid(self, data, expectation):
        response = Response(status_code=http.HTTPStatus.OK, body={'some': 'body'})
        response_validator = ResponseValidator(**data)

        with pytest.raises(ValueError) as e:
            response_validator.validate_response(response)

        assert e.exconly(tryshort=True) == expectation


class TestRouteMatch:
    @pytest.mark.parametrize(
        'data, expectation',
        [
            (
                {
                    'route': {'id': uuid.UUID('70850e6c-7755-4edc-8fc2-12caf5c3d8ca'), 'hits': 0, 'path': '/test'},
                    'http_method': http.HTTPMethod.GET,
                    'path_params': {},
                },
                {
                    'http_method': http.HTTPMethod.GET,
                    'path_params': {},
                    'route': {
                        'hits': 0,
                        'http_methods': [http.HTTPMethod.GET],
                        'id': uuid.UUID('70850e6c-7755-4edc-8fc2-12caf5c3d8ca'),
                        'path': '/test',
                        'response_selector': ResponseSelector.RANDOM,
                        'response_validators': [],
                        'responses': []
                    },
                }
            ),
            (
                {
                    'route': {'id': uuid.UUID('44450e6c-7755-4edc-8fc2-12caf5c3d8ca'), 'hits': 7, 'path': '/test'},
                    'http_method': 'GET',
                    'path_params': {'someparam': 'somevalue', 'anotherparam': [1, 2, 3]},
                },
                {
                    'http_method': http.HTTPMethod.GET,
                    'path_params': {'someparam': 'somevalue', 'anotherparam': [1, 2, 3]},
                    'route': {
                        'hits': 7,
                        'http_methods': [http.HTTPMethod.GET],
                        'id': uuid.UUID('44450e6c-7755-4edc-8fc2-12caf5c3d8ca'),
                        'path': '/test',
                        'response_selector': ResponseSelector.RANDOM,
                        'response_validators': [],
                        'responses': []
                    },
                }
            ),
        ]
    )
    def test_route_match_is_valid(self, data, expectation):
        route_match = RouteMatch(**data).model_dump()

        assert route_match == expectation


class TestResponseDelay:
    @pytest.mark.parametrize(
        'data, expectation',
        [
            ({}, (0, 0)),
            (1, (1, 1)),
            ([1, 3], (1, 3)),
            ((1, 2), (1, 2)),
            ({'min_delay': 0.25}, (0.25, 0.25)),
            ({'min_delay': 0.25, 'max_delay': 1}, (0.25, 1)),
        ]
    )
    def test_response_delay_valid(self, data, expectation):
        assert ResponseDelay.model_validate(data).model_dump() == expectation

    @pytest.mark.parametrize(
        'data, expectation',
        [
            ([1, 3, 4], 'Input of response delay must be a single value or list of two numbers.'),
            ([3, 1], 'Maximum delay (1s) must be greater than minimum delay (3s).'),
        ]
    )
    def test_response_delay_invalid(self, data, expectation):
        with pytest.raises(ValueError) as e:
            ResponseDelay.model_validate(data).model_dump()

            assert e.exconly(tryshort=True) == expectation

    def test_delay_response(self, mocker):
        response_delay = ResponseDelay(min_delay=1.57, max_delay=1.57)
        mocked_sleep = mocker.patch('time.sleep')

        response_delay.delay_response()
        mocked_sleep.assert_called_once_with(1.57)


class TestResponse:
    def test_as_fastapi_response(self):
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

    def test_delay_response(self, mocker):
        response = Response(
            status_code=http.HTTPStatus.OK,
            body={
                'foo': 'bar'
            },
            headers={
                'header': 'value'
            },
            delay={'min_delay': 1, 'max_delay': 1}
        )
        mocked_sleep = mocker.patch('time.sleep')

        response.delay_response()
        mocked_sleep.assert_called_once_with(1)


class TestResponseSelector:
    responses = [
        Response(status_code=http.HTTPStatus.OK, body={'body': 1}, hits=3),
        Response(status_code=http.HTTPStatus.OK, body={'body': 2}, hits=2),
        Response(status_code=http.HTTPStatus.OK, body={'body': 3}, hits=1),
        Response(status_code=http.HTTPStatus.OK, body={'body': 4}, hits=0),
        Response(status_code=http.HTTPStatus.OK, body={'body': 5}, hits=4),
    ]

    def test_select_response_valid_first(self):
        assert ResponseSelector.FIRST.select_response(self.responses) == self.responses[0]

    def test_select_response_valid_random(self):
        responses = copy.deepcopy(self.responses)
        random_state = random.getstate()
        random.seed(0)

        assert ResponseSelector.RANDOM.select_response(responses) == responses[4]

        random.seed(10)

        assert ResponseSelector.RANDOM.select_response(responses) == responses[2]

        random.setstate(random_state)

    def test_select_response_valid_balanced(self):
        responses = copy.deepcopy(self.responses)

        # Manually emulate balanced hits increasing and check if the next
        # response is selected in balanced manner
        assert ResponseSelector.BALANCED.select_response(responses) == responses[3]

        responses[3].hits += 1
        assert ResponseSelector.BALANCED.select_response(responses) == responses[2]

        responses[2].hits += 1
        assert ResponseSelector.BALANCED.select_response(responses) == responses[3]

        responses[3].hits += 1
        assert ResponseSelector.BALANCED.select_response(responses) == responses[1]

        responses[1].hits += 1
        assert ResponseSelector.BALANCED.select_response(responses) == responses[2]

    def test_select_response_invalid_responses(self):
        response_selector = ResponseSelector.FIRST

        with pytest.raises(ValueError) as e:
            response_selector.select_response([])

        assert e.exconly(tryshort=True) == 'ValueError: No suitable response found.'


class TestRoute:
    responses = [
        Response(status_code=http.HTTPStatus.OK, body={'body': 1}, hits=3),
        Response(status_code=http.HTTPStatus.OK, body={'body': 4}, hits=0),
        Response(status_code=http.HTTPStatus.OK, body={'body': 5}, hits=4),
    ]

    response_validators = [
        ResponseValidator(
            status_code=http.HTTPStatus.OK,
            json_schema={
                '$schema': 'https://json-schema.org/draft/2020-12/schema',
                'properties': {'body': {'type': 'number'}}
            },
        ),
        ResponseValidator(
            status_code=http.HTTPStatus.OK,
            json_schema={
                '$schema': 'https://json-schema.org/draft/2020-12/schema',
                'properties': {'body': {'type': 'string'}}
            },
        )
    ]

    def test_validate_existing_response_validators_combinations(self):
        route = Route(
            path='test', responses=self.responses, response_validators=self.response_validators,
            http_methods=[http.HTTPMethod.GET]
        )

        assert route.validate_existing_response_validator_combinations() is None

    def test_validate_new_response_validator(self):
        route = Route(path='test', responses=self.responses, http_methods=[http.HTTPMethod.GET])

        assert route.validate_new_response_validator(self.response_validators[0]) is None

    def test_validate_new_response(self):
        route = Route(
            path='test', responses=[], response_validators=self.response_validators, http_methods=[http.HTTPMethod.GET]
        )

        for response in self.responses:
            assert route.validate_new_response(response) is None

    def test_validate_new_response_raises(self):
        response_validator = ResponseValidator(
            status_code=http.HTTPStatus.OK,
            json_schema={
                '$schema': 'https://json-schema.org/draft/2020-12/schema',
                'properties': {'body': {'type': 'string'}}
            },
        )
        route = Route(
            path='test', responses=[], response_validators=[response_validator], http_methods=[http.HTTPMethod.GET]
        )

        with pytest.raises(ValueError) as e:
            route.validate_new_response(self.responses[0])

        assert e.exconly(tryshort=True) == \
               f'ValueError: Response "{self.responses[0].id}" doesn\'t match ony of the configured validators.'

    def test_validate_new_response_empty(self):
        route = Route(path='test', responses=[], http_methods=[http.HTTPMethod.GET])

        assert route.validate_new_response(self.responses[0]) is None

    def test_match(self):
        route = Route(path='test', responses=self.responses, http_methods=[http.HTTPMethod.GET])
        mocked_request_match = cast(Request, MockedRequest('GET', {'path': 'test'}))
        mocked_request_no_match = cast(Request, MockedRequest('PATCH', {'path': 'test'}))

        assert route.match(mocked_request_match) == (http.HTTPMethod.GET, {})
        assert route.match(mocked_request_no_match) is None

    def test_match_method(self):
        route = Route(
            path='test', responses=[],
            http_methods=[http.HTTPMethod.GET, http.HTTPMethod.POST, http.HTTPMethod.DELETE]
        )

        assert route.match_method('POST') == http.HTTPMethod.POST
        assert route.match_method('GET') == http.HTTPMethod.GET
        assert route.match_method('PATCH') is None

    def test_get_response(self, mocker):
        route = Route(
            path='test',
            responses=self.responses,
            response_selector=ResponseSelector.FIRST,
            http_methods=[http.HTTPMethod.GET],
        )

        assert route.get_response(mocker) == self.responses[0]

    def test_get_response_by_id(self):
        route = Route(
            path='test',
            responses=self.responses,
            response_selector=ResponseSelector.FIRST,
            http_methods=[http.HTTPMethod.GET],
        )

        assert route.get_response_by_id(self.responses[2].id) == self.responses[2]
        assert route.get_response_by_id(uuid.uuid4()) is None

    def test_get_response_validator_by_id(self):
        route = Route(
            path='test',
            responses=self.responses,
            response_selector=ResponseSelector.FIRST,
            response_validators=self.response_validators,
            http_methods=[http.HTTPMethod.GET],
        )

        assert route.get_response_validator_by_id(self.response_validators[0].id) == self.response_validators[0]
        assert route.get_response_validator_by_id(uuid.uuid4()) is None


class TestHealthcheckStatus:
    @pytest.mark.parametrize(
        'data',
        [
            {},
            {'status': 'OK'},
        ]
    )
    def test_healthcheck_status(self, data):
        assert HealthcheckStatus(**data).model_dump() == {'status': 'OK'}


class TestInputResponseValidator:
    @pytest.mark.parametrize(
        'data, expectation',
        [
            ({'status_code': 200, 'json_schema': {}}, {'status_code': 200, 'json_schema': {}}),
            (
                {
                    'status_code': 200,
                    'json_schema': {
                        '$schema': 'https://json-schema.org/draft/2020-12/schema',
                        'properties': {'some': {'type': 'string'}}
                    }
                },
                {
                    'status_code': 200,
                    'json_schema': {
                        '$schema': 'https://json-schema.org/draft/2020-12/schema',
                        'properties': {'some': {'type': 'string'}}
                    }
                }
            )
        ]
    )
    def test_input_response_validator(self, data, expectation):
        assert InputResponseValidator(**data).model_dump() == expectation


class TestInputResponse:
    @pytest.mark.parametrize(
        'data, expectation',
        [
            (
                {
                    'status_code': 200,
                    'body': {},
                },
                {
                    'body': {},
                    'delay': (0, 0),
                    'headers': {},
                    'status_code': 200,
                    'weight': 1
                }
            ),
            (
                {
                    'status_code': 200,
                    'body': {'body_field_name': 'value'},
                    'delay': {'min_delay': 0.05, 'max_delay': 0.25},
                    'headers': {'User-Agent': 'Mozilla/007'},
                    'weight': 0.5
                },
                {
                    'body': {'body_field_name': 'value'},
                    'delay': (0.05, 0.25),
                    'headers': {'User-Agent': 'Mozilla/007'},
                    'status_code': 200,
                    'weight': 0.5
                }
            )
        ]
    )
    def test_input_response(self, data, expectation):
        assert InputResponse(**data).model_dump() == expectation


class TestInputRoute:
    @pytest.mark.parametrize(
        'data, expectation',
        [
            (
                {
                    'path': '/test',
                },
                {
                    'http_methods': [http.HTTPMethod.GET],
                    'path': '/test',
                    'response_selector': ResponseSelector.RANDOM,
                    'response_validators': [],
                    'responses': []
                }
            ),
            (
                {
                    'path': '/test',
                    'responses': []
                },
                {
                    'http_methods': [http.HTTPMethod.GET],
                    'path': '/test',
                    'response_selector': ResponseSelector.RANDOM,
                    'response_validators': [],
                    'responses': []
                }
            ),
            (
                {
                    'path': '/test',
                    'responses': [{'status_code': 200, 'body': {}}],
                },
                {
                    'http_methods': [http.HTTPMethod.GET],
                    'path': '/test',
                    'response_selector': ResponseSelector.RANDOM,
                    'response_validators': [],
                    'responses': [
                        {
                            'body': {},
                            'delay': (0, 0),
                            'headers': {},
                            'status_code': http.HTTPStatus.OK,
                            'weight': 1
                        }
                    ],
                }
            ),
            (
                {
                    'path': '/test',
                    'responses': [{'status_code': 200, 'body': {}}],
                    'http_methods': [http.HTTPMethod.POST],
                    'response_validators': [
                        ResponseValidator(
                            id=uuid.UUID('e647ef2e-a945-4649-a8ea-5deccaf159e5'),
                            status_code=http.HTTPStatus.OK,
                            json_schema={
                                '$schema': 'https://json-schema.org/draft/2020-12/schema',
                                'properties': {'body': {'type': 'number'}}
                            },
                        ),
                        ResponseValidator(
                            id=uuid.UUID('ec2a2765-2fc0-4aa1-9fd5-2b6f2385d82d'),
                            status_code=http.HTTPStatus.OK,
                            json_schema={
                                '$schema': 'https://json-schema.org/draft/2020-12/schema',
                                'properties': {'body': {'type': 'string'}}
                            },
                        )
                    ],
                    'response_selector': ResponseSelector.FIRST,
                },
                {
                    'http_methods': [http.HTTPMethod.POST],
                    'path': '/test',
                    'response_selector': ResponseSelector.FIRST,
                    'response_validators': [
                        {
                            'id': uuid.UUID('e647ef2e-a945-4649-a8ea-5deccaf159e5'),
                            'status_code': http.HTTPStatus.OK,
                            'json_schema': {
                                '$schema': 'https://json-schema.org/draft/2020-12/schema',
                                'properties': {'body': {'type': 'number'}}
                            },
                        },
                        {
                            'id': uuid.UUID('ec2a2765-2fc0-4aa1-9fd5-2b6f2385d82d'),
                            'status_code': http.HTTPStatus.OK,
                            'json_schema': {
                                '$schema': 'https://json-schema.org/draft/2020-12/schema',
                                'properties': {'body': {'type': 'string'}}
                            },
                        }
                    ],
                    'responses': [
                        {
                            'body': {},
                            'delay': (0, 0),
                            'headers': {},
                            'status_code': http.HTTPStatus.OK,
                            'weight': 1
                        }
                    ],
                }
            ),
        ]
    )
    def test_input_route(self, data, expectation):
        assert InputRoute(**data).model_dump() == expectation
