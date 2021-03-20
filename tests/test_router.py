import re
from collections import OrderedDict

import pytest
import flask

from trickster.auth import NoAuth
from trickster import RouteConfigurationError
from trickster.router import Delay, Response, ResponseSelectionStrategy, Route
from trickster.input import IncommingTestRequest


@pytest.mark.unit
class TestDelay:
    def test_deserialize_empty(self):
        delay = Delay.deserialize(None)
        assert delay.min_delay == 0.0
        assert delay.max_delay == 0.0

    def test_deserialize_not_empty(self):
        delay = Delay.deserialize([1.2, 3.4])
        assert delay.min_delay == 1.2
        assert delay.max_delay == 3.4

    def test_deserialize_invalid(self):
        with pytest.raises(RouteConfigurationError):
            delay = Delay.deserialize([3.4, 1.2])

    def test_serialize_empty(self):
        delay = Delay()
        assert delay.serialize() == None

    def test_deserialize_not_empty(self):
        delay = Delay(1.2, 3.4)
        assert delay.serialize() == [1.2, 3.4]

    def test_wait(self, mocker):
        sleep = mocker.patch('time.sleep')
        delay = Delay(1.2, 3.4)
        delay.wait()
        sleep.assert_called_once()

    def test_wait_default(self, mocker):
        sleep = mocker.patch('time.sleep')
        delay = Delay()
        delay.wait()
        sleep.assert_called_once_with(0)


@pytest.mark.unit
class TestResponse:
    def test_deserialize_complete(self):
        response = Response.deserialize({
            'id': 'id',
            'status': 400,
            'weight': 0.3,
            'repeat': 3,
            'delay': [0.1, 0.2],
            'headers': {
                'content-type': 'application/json'
            },
            'body': {
                'works': True
            }
        })

        assert response.id == 'id'
        assert response.status == 400
        assert response.weight == 0.3
        assert response.repeat == 3
        assert isinstance(response.delay, Delay)
        assert response.delay.min_delay == 0.1
        assert response.delay.max_delay == 0.2
        assert response.headers == {
            'content-type': 'application/json'
        }
        assert response.body == {
            'works': True
        }

    def test_deserialize_minimal(self):
        response = Response.deserialize({
            'id': 'id',
            'body': '',
        })
        assert response.id == 'id'
        assert response.status == 200
        assert response.weight == 0.5
        assert response.repeat == None
        assert isinstance(response.delay, Delay)
        assert response.delay.min_delay == 0.0
        assert response.delay.max_delay == 0.0
        assert response.headers == {}
        assert response.body == ""

    @pytest.mark.parametrize('body', [{}, 1, True])
    def test_add_automatic_json_header(self, body):
        response = Response.deserialize({
            'id': 'id',
            'body': body
        })
        assert response.headers == {'content-type': 'application/json'}

    @pytest.mark.parametrize('body', [{}, 1, True])
    def test_doesnt_add_json_header_when_user_specifies_headers(self, body):
        response = Response.deserialize({
            'id': 'id',
            'body': body,
            'headers': {}
        })
        assert response.headers == {}

    def test_doesnt_add_json_header_to_string(self):
        response = Response.deserialize({
            'id': 'id',
            'body': 'string'
        })
        assert response.headers == {}

    def test_use(self):
        response = Response('id', '', Delay(), repeat=1)
        assert response.is_active
        assert response.used_count == 0
        assert response.repeat == 1
        response.use()
        assert not response.is_active
        assert response.used_count == 1
        assert response.repeat == 1

    def test_wait(self, mocker):
        response = Response('id', '', Delay(1.0, 2.0))
        sleep = mocker.patch('time.sleep')
        response.wait()
        sleep.assert_called_once()

    def test_serialized_body_returns_strings_as_inserted(self):
        response = Response('id', 'string', Delay())
        response.serialized_body == 'string'

    def test_serialized_body_returns_json_as_string(self):
        response = Response('id', {'key': 'value'}, Delay())
        response.serialized_body == '{"key": "value"}'

    def test_serialize_deserialize_complete(self):
        response = Response.deserialize({
            'id': 'id',
            'status': 400,
            'weight': 0.3,
            'repeat': 3,
            'delay': [0.1, 0.2],
            'headers': {
                'content-type': 'application/json'
            },
            'body': {
                'works': True
            }
        })

        assert response.serialize() == {
            'id': 'id',
            'status': 400,
            'weight': 0.3,
            'repeat': 3,
            'delay': [0.1, 0.2],
            'is_active': True,
            'used_count': 0,
            'headers': {
                'content-type': 'application/json'
            },
            'body': {
                'works': True
            }
        }

    def test_as_flask_response(self):
        response = Response(
            'id', {'key': 'value'}, Delay(), headers={'header': 'header_value'}
        )

        flask_response = response.as_flask_response()
        assert isinstance(flask_response, flask.Response)
        assert flask_response.status_code == 200
        assert flask_response.data == b'{"key": "value"}'
        assert flask_response.headers['header'] == 'header_value'


@pytest.mark.unit
class TestResponseSelectionStrategy:
    def test_deserialize(self):
        strategy = ResponseSelectionStrategy.deserialize('cycle')
        assert strategy == ResponseSelectionStrategy.cycle

        strategy = ResponseSelectionStrategy.deserialize('random')
        assert strategy == ResponseSelectionStrategy.random

        strategy = ResponseSelectionStrategy.deserialize('greedy')
        assert strategy == ResponseSelectionStrategy.greedy

    def test_default_strategy_is_greedy(self):
        strategy = ResponseSelectionStrategy.deserialize()
        assert strategy == ResponseSelectionStrategy.greedy

    def test_serialize(self):
        assert ResponseSelectionStrategy.cycle.serialize() == 'cycle'
        assert ResponseSelectionStrategy.random.serialize() == 'random'
        assert ResponseSelectionStrategy.greedy.serialize() == 'greedy'

    def test_greedy_selection(self):
        strategy = ResponseSelectionStrategy.greedy
        r1 = Response('id1', '', Delay(), repeat=2)
        r2 = Response('id2', '', Delay(), repeat=2)

        assert strategy.select_response([r1, r2]) is r1
        r1.use()
        assert strategy.select_response([r1, r2]) is r1
        r1.use()
        assert strategy.select_response([r1, r2]) is r2
        r2.use()
        assert strategy.select_response([r1, r2]) is r2
        r2.use()
        assert strategy.select_response([r1, r2]) is None

    def test_cycle_selection(self):
        strategy = ResponseSelectionStrategy.cycle
        r1 = Response('id1', '', Delay(), repeat=2)
        r2 = Response('id2', '', Delay(), repeat=3)

        assert strategy.select_response([r1, r2]) is r1
        r1.use()
        assert strategy.select_response([r1, r2]) is r2
        r2.use()
        assert strategy.select_response([r1, r2]) is r1
        r1.use()
        assert strategy.select_response([r1, r2]) is r2
        r2.use()
        assert strategy.select_response([r1, r2]) is r2
        r2.use()
        assert strategy.select_response([r1, r2]) is None

    def test_random_selection(self):
        strategy = ResponseSelectionStrategy.random
        r1 = Response('id1', '', Delay(), weight=0.4)
        r2 = Response('id2', '', Delay(), weight=0.6)

        for i in range(250):
            response = strategy.select_response([r1, r2])
            response.use()

        assert r1.used_count < r2.used_count


@pytest.mark.unit
class TestRoute:
    def test_deserialize_complete(self):
        route = Route.deserialize({
            'id': 'id1',
            'path': '/endpoint_\\w*',
            'method': 'GET',
            'auth': {
                'method': 'basic',
                'username': 'username',
                'password': 'password'
            },
            'response_selection': 'random',
            'responses': [
                {
                    'id': 'response_1',
                    'body': {
                        'works': True
                    }
                }
            ]
        })

        assert route.id == 'id1'
        assert isinstance(route.path, re.Pattern)
        assert route.method == 'GET'
        assert route.auth.method == 'basic'
        assert route.response_selection == ResponseSelectionStrategy.random

    def test_deserialize_minimal(self):
        route = Route.deserialize({
            'id': 'id1',
            'path': '/endpoint_\\w*',
            'responses': [
                {
                    'body': ''
                }
            ]
        })

        assert route.id == 'id1'
        assert isinstance(route.path, re.Pattern)
        assert route.method == 'GET'
        assert isinstance(route.auth, NoAuth)
        assert route.response_selection == ResponseSelectionStrategy.greedy

    def test_deserialize_duplicate_response_ids(self):
        with pytest.raises(RouteConfigurationError):
            route = Route.deserialize({
                'id': 'id1',
                'path': '/endpoint_\\w*',
                'responses': [
                    {
                        'id': 'duplicate',
                        'body': ''
                    },
                    {
                        'id': 'duplicate',
                        'body': ''
                    }
                ]
            })

    def test_deserialize(self):
        route = Route(
            id='id1',
            responses=OrderedDict(),
            response_selection=ResponseSelectionStrategy.random,
            path=re.compile(r'/test.*'),
            auth=NoAuth(),
            method='GET'
        )

        assert route.serialize() == {
            'id': 'id1',
            'responses': [],
            'response_selection': 'random',
            'path': '/test.*',
            'auth': None,
            'method': 'GET',
            'used_count': 0
        }

    def test_get_response_found(self):
        r1 = Response('id1', 'string', Delay())
        r2 = Response('id2', 'string', Delay())
        route = Route(
            id='id1',
            responses=OrderedDict({
                'id1': r1,
                'id2': r2
            }),
            response_selection=ResponseSelectionStrategy.random,
            path=re.compile(r'/test.*'),
            auth=NoAuth(),
            method='GET'
        )

        assert route.get_response('id1') is r1

    def test_get_response_not_found(self):
        r1 = Response('id1', 'string', Delay())
        route = Route(
            id='id1',
            responses=OrderedDict({'id1': r1}),
            response_selection=ResponseSelectionStrategy.random,
            path=re.compile(r'/test.*'),
            auth=NoAuth(),
            method='GET'
        )

        assert route.get_response('id3') is None

    def test_use(self):
        response = Response('id1', 'string', Delay())
        route = Route(
            id='id1',
            responses=OrderedDict({'id1': response}),
            response_selection=ResponseSelectionStrategy.random,
            path=re.compile(r'/test.*'),
            auth=NoAuth(),
            method='GET'
        )

        route.use(response)
        assert route.used_count == 1
        assert response.used_count == 1

    def test_use_without_response(self):
        route = Route(
            id='id1',
            responses=OrderedDict(),
            response_selection=ResponseSelectionStrategy.random,
            path=re.compile(r'/test.*'),
            auth=NoAuth(),
            method='GET'
        )

        route.use(None)
        assert route.used_count == 1

    def test_match(self):
        route = Route(
            id='id1',
            responses=OrderedDict(),
            response_selection=ResponseSelectionStrategy.random,
            path=re.compile(r'/test.*'),
            auth=NoAuth(),
            method='GET'
        )
        request = IncommingTestRequest(
            base_url='http://localhost/',
            full_path='/test_url',
            method='GET'
        )
        assert route.match(request)
