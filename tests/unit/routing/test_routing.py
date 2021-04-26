import pytest

import flask

from trickster.routing import RouteConfigurationError, ResponseContext, JsonResponseBody, ResponseBody
from trickster.routing.router import Delay, Response


@pytest.mark.unit
class TestDelay:
    def test_deserialize_delay_from_none(self):
        delay = Delay.deserialize(None)
        assert delay.min_delay == 0.0
        assert delay.max_delay == 0.0

    def test_deserialize_delay_from_list(self):
        delay = Delay.deserialize([1.2, 3.4])
        assert delay.min_delay == 1.2
        assert delay.max_delay == 3.4

    def test_deserialize_delay_from_single_number(self):
        delay = Delay.deserialize(1.2)
        assert delay.min_delay == 1.2
        assert delay.max_delay == 1.2

    def test_deserialize_min_larger_than_max(self):
        with pytest.raises(RouteConfigurationError):
            delay = Delay.deserialize([3.4, 1.2])

    def test_serialize_without_arguments(self):
        delay = Delay()
        assert delay.serialize() == 0.0

    def test_serialize_min_and_max(self):
        delay = Delay(1.2, 3.4)
        assert delay.serialize() == [1.2, 3.4]

    def test_serialize_min_and_max_equal(self):
        delay = Delay(1.2, 1.2)
        assert delay.serialize() == 1.2

    def test_wait_calls_sleep(self, mocker):
        sleep = mocker.patch('time.sleep')
        delay = Delay(1.2, 3.4)
        delay.wait()
        sleep.assert_called_once()

    def test_wait_with_empty_delay_calls_sleep_with_0(self, mocker):
        sleep = mocker.patch('time.sleep')
        delay = Delay()
        delay.wait()
        sleep.assert_called_once_with(0)


@pytest.mark.unit
class TestResponse:
    def test_deserialize_complete(self):
        response = Response.deserialize({
            'status': 400,
            'delay': [0.1, 0.2],
            'headers': {
                'content-type': 'application/json'
            },
            'body': {
                'works': True
            }
        })

        assert response.status == 400
        assert isinstance(response.delay, Delay)
        assert response.delay.min_delay == 0.1
        assert response.delay.max_delay == 0.2
        assert response.headers == {
            'content-type': 'application/json'
        }
        assert isinstance(response.body, ResponseBody)
        assert response.body.content == {
            'works': True
        }

    def test_deserialize_minimal(self):
        response = Response.deserialize({
            'body': '',
        })
        assert response.status == 200
        assert isinstance(response.delay, Delay)
        assert response.delay.min_delay == 0.0
        assert response.delay.max_delay == 0.0
        assert response.headers == {}
        assert isinstance(response.body, ResponseBody)
        assert response.body.content == ''

    @pytest.mark.parametrize('body', [{}, [], 1, True])
    def test_add_automatic_json_header(self, body):
        response = Response.deserialize({
            'body': body
        })
        assert response.headers == {'content-type': 'application/json'}

    @pytest.mark.parametrize('body', [{}, [], 1, True])
    def test_doesnt_add_json_header_when_user_specifies_headers(self, body):
        response = Response.deserialize({
            'body': body,
            'headers': {}
        })
        assert response.headers == {}

    def test_doesnt_add_json_header_to_string(self):
        response = Response.deserialize({
            'body': 'string'
        })
        assert response.headers == {}

    def test_use(self):
        response = Response(ResponseBody(''), Delay())
        assert response.used_count == 0
        response.use()
        assert response.used_count == 1

    def test_wait(self, mocker):
        response = Response(ResponseBody(''), Delay(1.0, 2.0))
        sleep = mocker.patch('time.sleep')
        response.wait()
        sleep.assert_called_once()

    def test_serialize_body_returns_strings_as_inserted(self):
        context = ResponseContext()
        response = Response(ResponseBody('string'), Delay())
        response.body.as_flask_response(context) == 'string'

    def test_serialize_body_returns_json_as_string(self):
        context = ResponseContext()
        response = Response(JsonResponseBody({'key': 'value'}), Delay())
        response.body.as_flask_response(context) == '{"key": "value"}'

    def test_serialize_deserialize_complete(self):
        response = Response.deserialize({
            'status': 400,
            'delay': [0.1, 0.2],
            'headers': {
                'content-type': 'application/json'
            },
            'body': {
                'works': True
            }
        })

        assert response.serialize() == {
            'status': 400,
            'delay': [0.1, 0.2],
            'used_count': 0,
            'headers': {
                'content-type': 'application/json'
            },
            'body': {
                'works': True
            }
        }

    def test_as_flask_response(self):
        context = ResponseContext()
        response = Response(
            JsonResponseBody({'key': 'value'}), Delay(), headers={'header': 'header_value'}
        )

        flask_response = response.as_flask_response(context)
        assert isinstance(flask_response, flask.Response)
        assert flask_response.status_code == 200
        assert flask_response.data == b'{"key": "value"}'
        assert flask_response.headers['header'] == 'header_value'


@pytest.mark.unit
class TestResponseContext:
    def test_get_variable(self):
        context = ResponseContext()
        context['key'] = 'value'
        assert context.get('$.key') == 'value'

    def test_get_variable_missing(self):
        context = ResponseContext()
        assert context.get('$.key') is None

    def test_get_variable_deep(self):
        context = ResponseContext()
        context['key1'] = {
            'key2': {
                'key3': 'value'
            }
        }
        assert context.get('$.key1.key2.key3') == 'value'

    def test_get_variable_dict(self):
        context = ResponseContext()
        context['key1'] = {
            'key2': {
                'key3': 'value'
            }
        }
        assert context.get('$.key1.key2') == {
            'key3': 'value'
        }

    def test_get_variable_multiple(self):
        context = ResponseContext()
        context['key1'] = 'value1'
        context['key2'] = 'value2'
        assert context.get('key1|key2') == ['value1', 'value2']

    def test_get_item_original(self):
        context = ResponseContext()
        context['key1'] = [1, 2]
        assert context['key1'] == [1, 2]


@pytest.mark.unit
class TestResponseBody:
    def test_serialize(self):
        response_body = ResponseBody('text')
        assert response_body.serialize() == 'text'

    def test_as_flask_response(self):
        response_body = ResponseBody('text')
        assert response_body.as_flask_response(ResponseContext()) == 'text'

    def test_default_headers(self):
        response_body = ResponseBody('text')
        assert response_body.default_headers == {}

    def test_deserialize_raw(self):
        response_body = ResponseBody.deserialize('text')
        assert isinstance(response_body, ResponseBody)
        assert response_body.content == 'text'

    def test_deserialize_json(self):
        response_body = ResponseBody.deserialize({'key': 'value'})
        assert isinstance(response_body, JsonResponseBody)
        assert response_body.content == {'key': 'value'}

@pytest.mark.unit
class TestJsonResponseBody:
    def test_serialize(self):
        response_body = JsonResponseBody({'key': 'value'})
        assert response_body.serialize() == {'key': 'value'}

    def test_as_flask_response(self):
        response_body = JsonResponseBody({'key': 'value'})
        assert response_body.as_flask_response(ResponseContext()) == '{"key": "value"}'

    def test_as_flask_response_dynamic_dict_attr(self):
        response_body = JsonResponseBody({
            'key': {'$ref': '$.key'}
        })
        context = ResponseContext()
        context['key'] = 'value'
        assert response_body.as_flask_response(context) == '{"key": "value"}'

    def test_as_flask_response_dynamic_list_item(self):
        response_body = JsonResponseBody({
            'list': [
                {'$ref': '$.key1'},
                {'$ref': '$.key2'}
            ]
        })
        context = ResponseContext()
        context['key1'] = 'value1'
        context['key2'] = 'value2'
        assert response_body.as_flask_response(context) == '{"list": ["value1", "value2"]}'

    def test_default_headers(self):
        response_body = JsonResponseBody({'key': 'value'})
        assert response_body.default_headers == {'content-type': 'application/json'} 

    @pytest.mark.parametrize('payload', [
        {'$ref': '$.key1 + $.key2'},
        [{'$ref': 'invalid payload'}],
        {'key': {'$ref': 'invalid payload'}}
    ])
    def test_raises_error_when_created_with_invalid_payload(self, payload):
        with pytest.raises(RouteConfigurationError):
            JsonResponseBody(payload)
