import http
import copy
import random
import uuid

import pytest
from fastapi import Request

from trickster.model import ParametrizedPath, Response, Route, ResponseDelay, ResponseValidator, ResponseSelector

from typing import cast


class MockedRequest:
    def __init__(self, method: str, path_params: dict[str, str]) -> None:
        self.method = method
        self.path_params = path_params


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

    def test_validate_invalid(self):
        with pytest.raises(ValueError):
            ParametrizedPath.validate_model(True)

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

    @pytest.mark.xfail
    def test_serialize_model(self):
        # TODO: Dig deeper into the class
        # Probably     @field_validator('path') should be used in validate_model
        path = ParametrizedPath(path='some/path')

        assert path.serialize_model() == 'some/path'

    def test_path_regex(self):
        ...


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


class TestResponseDelay:
    def test_serialize_model(self):
        response_delay = ResponseDelay(min_delay=1, max_delay=2)

        assert response_delay.serialize_model() == (1, 2)

    @pytest.mark.parametrize(
        'test_data, expectation',
        [
            pytest.param(
                {'min_delay': 0.2, 'max_delay': 1},
                {'min_delay': 0.2, 'max_delay': 1},
                id='Valid values in a dict'
            ),
            pytest.param(
                0.1,
                {'min_delay': 0.1, 'max_delay': 0.1},
                id='Single valid value'
            ),
            pytest.param(
                (0.2, 1),
                {'min_delay': 0.2, 'max_delay': 1},
                id='Valid values in a tuple'
            ),
        ]
    )
    def test_validate_model_valid(self, test_data, expectation):
        assert ResponseDelay.validate_model(test_data) == expectation

    @pytest.mark.parametrize(
        'test_data, expectation',
        [
            pytest.param(
                (3, 1),
                'ValueError: Maximum delay',
                id='Min value > max value'
            ),
            pytest.param(
                (1, 2, 3),
                'ValueError: Input of response delay must be a single value',
                id='More than 2 values'
            ),
            pytest.param(
                {'some_value': True, 'another_value': 2},
                'ValueError: Input of response delay must be a single value',
                marks=pytest.mark.xfail,
                id='Dict with invalid values'
            ),
            pytest.param(
                'Single_value',
                'ValueError: Input of response delay must be a single value',
                id='Single invalid value'
            )
        ]
    )
    def test_validate_model_invalid(self, test_data, expectation):
        with pytest.raises(ValueError) as e:
            ResponseDelay.validate_model(test_data)

        assert e.exconly(tryshort=True).startswith(expectation)

    def test_delay_response(self, mocker):
        response_delay = ResponseDelay(min_delay=1, max_delay=1)
        mocked_sleep = mocker.patch('time.sleep')

        response_delay.delay_response()
        mocked_sleep.assert_called_once_with(1)


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
    def test_validate_response_invalid(self, data, expectation, mocker):
        response = Response(status_code=http.HTTPStatus.OK, body={'some': 'body'})
        response_validator = ResponseValidator(**data)

        with pytest.raises(ValueError) as e:
            response_validator.validate_response(response)

        assert e.exconly(tryshort=True) == expectation


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
        responses[2].hits += 1

    def test_select_response_invalid_responses(self):
        response_selector = ResponseSelector.FIRST

        with pytest.raises(ValueError) as e:
            response_selector.select_response([])

        assert e.exconly(tryshort=True) == 'ValueError: No suitable response found.'

    @pytest.mark.xfail
    def test_select_response_invalid_algo(self):
        with pytest.raises(ValueError) as e:
            ResponseSelector.INVALIDALGO.select_response(self.responses)

        assert e.exconly(tryshort=True) == 'Response selection algorithm for InvalidAlgo is not configured.'


class TestRoute:
    responses = [
        Response(status_code=http.HTTPStatus.OK, body={'body': 1}, hits=3),
        Response(status_code=http.HTTPStatus.OK, body={'body': 'two'}, hits=2),
        Response(id=uuid.uuid4(), status_code=http.HTTPStatus.OK, body={'body': 3}, hits=1),
        Response(status_code=http.HTTPStatus.OK, body={'body': 4}, hits=0),
        Response(status_code=http.HTTPStatus.OK, body={'body': 5}, hits=4),
    ]

    @pytest.mark.xfail
    def test_validate_model(self):
        ...

    def test_validate_existing_response_validatos_combinations(self):
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
        route = Route(path='test', responses=self.responses, response_validators=response_validators, http_methods=[http.HTTPMethod.GET])

        assert route.validate_existing_response_validator_combinations() is None

    def test_validate_new_response_validator(self):
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
        route = Route(path='test', responses=self.responses, response_validators=response_validators, http_methods=[http.HTTPMethod.GET])

        assert route.validate_new_response_validator(response_validators[0]) is None

    def test_validate_new_response(self):
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
        route = Route(path='test', responses=[], response_validators=response_validators, http_methods=[http.HTTPMethod.GET])

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
        route = Route(path='test', responses=[], response_validators=[response_validator], http_methods=[http.HTTPMethod.GET])

        with pytest.raises(ValueError) as e:
            route.validate_new_response(self.responses[0])

        assert e.exconly(tryshort=True) == f'ValueError: Response "{self.responses[0].id}" doesn\'t match ony of the configured validators.'

    def test_validate_new_response_empty(self):
        route = Route(path='test', responses=[], http_methods=[http.HTTPMethod.GET])

        assert route.validate_new_response(self.responses[0]) is None

    def test_match(self):
        route = Route(path='test', responses=self.responses, http_methods=[http.HTTPMethod.GET])
        mocked_request = cast(Request, MockedRequest('GET', {'path': 'test'}))
        mocked_request_two = cast(Request, MockedRequest('PATCH', {'path': 'test'}))

        assert route.match(mocked_request) == (http.HTTPMethod.GET, {})
        assert route.match(mocked_request_two) is None

    def test_match_method(self):
        route = Route(path='test', responses=[], http_methods=[http.HTTPMethod.GET])
        assert route.match_method('GET') == http.HTTPMethod.GET

    def test_match_method_from_multiple(self):
        route = Route(path='test', responses=[], http_methods=[http.HTTPMethod.GET, http.HTTPMethod.POST])
        assert route.match_method('POST') == http.HTTPMethod.POST

    def test_match_method_with_no_match(self):
        route = Route(path='test', responses=[], http_methods=[http.HTTPMethod.GET])
        assert route.match_method('POST') is None

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

    def test_get_response_validator_by_id(self, mocker):
        validators = [
            ResponseValidator(
                status_code=http.HTTPStatus.OK,
                json_schema={
                    '$schema': 'https://json-schema.org/draft/2020-12/schema',
                    'properties': {'some': {'type': 'string'}}
                },
            ),
            ResponseValidator(
                status_code=http.HTTPStatus.OK,
                json_schema={
                    '$schema': 'https://json-schema.org/draft/2020-12/schema',
                    'properties': {'some': {'type': 'string'}}
                },
            ),
        ]
        route = Route(
            path='test',
            responses=self.responses,
            response_selector=ResponseSelector.FIRST,
            response_validators=validators,
            http_methods=[http.HTTPMethod.GET],
        )

        assert route.get_response_validator_by_id(validators[0].id) == validators[0]
        assert route.get_response_validator_by_id(uuid.uuid4()) is None
