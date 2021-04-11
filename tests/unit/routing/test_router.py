import re

import pytest
import flask

from trickster.routing import DuplicateRouteError, MissingRouteError, RouteConfigurationError
from trickster.routing.auth import NoAuth
from trickster.routing.router import Delay, Response, RouteResponse, ResponseSelectionStrategy, Route, Router
from trickster.routing.input import IncomingTestRequest


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
        assert response.body == {
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
        assert response.body == ''

    @pytest.mark.parametrize('body', [{}, 1, True])
    def test_add_automatic_json_header(self, body):
        response = Response.deserialize({
            'body': body
        })
        assert response.headers == {'content-type': 'application/json'}

    @pytest.mark.parametrize('body', [{}, 1, True])
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
        response = Response('', Delay())
        assert response.used_count == 0
        response.use()
        assert response.used_count == 1

    def test_wait(self, mocker):
        response = Response('', Delay(1.0, 2.0))
        sleep = mocker.patch('time.sleep')
        response.wait()
        sleep.assert_called_once()

    def test_serialized_body_returns_strings_as_inserted(self):
        response = Response('string', Delay())
        response.serialized_body == 'string'

    def test_serialized_body_returns_json_as_string(self):
        response = Response('id', {'key': 'value'}, Delay())
        response.serialized_body == '{"key": "value"}'

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
        response = Response(
            {'key': 'value'}, Delay(), headers={'header': 'header_value'}
        )

        flask_response = response.as_flask_response()
        assert isinstance(flask_response, flask.Response)
        assert flask_response.status_code == 200
        assert flask_response.data == b'{"key": "value"}'
        assert flask_response.headers['header'] == 'header_value'



@pytest.mark.unit
class TestRouteResponse:
    def test_deserialize_complete(self):
        response = RouteResponse.deserialize({
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
        response = RouteResponse.deserialize({
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
        assert response.body == ''

    def test_use(self):
        response = RouteResponse('id', '', Delay(), repeat=1)
        assert response.is_active
        assert response.used_count == 0
        assert response.repeat == 1
        response.use()
        assert not response.is_active
        assert response.used_count == 1
        assert response.repeat == 1

    def test_serialize_deserialize_complete(self):
        response = RouteResponse.deserialize({
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
        r1 = RouteResponse('id1', '', Delay(), repeat=2)
        r2 = RouteResponse('id2', '', Delay(), repeat=2)

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
        r1 = RouteResponse('id1', '', Delay(), repeat=2)
        r2 = RouteResponse('id2', '', Delay(), repeat=3)

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
        r1 = RouteResponse('id1', '', Delay(), weight=0.4)
        r2 = RouteResponse('id2', '', Delay(), weight=0.6)

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
        assert route.is_active == True

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
        assert route.is_active == True

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
            responses=[],
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
            'used_count': 0,
            'is_active': False
        }

    def test_get_response_found(self):
        r1 = RouteResponse('id1', 'string', Delay())
        r2 = RouteResponse('id2', 'string', Delay())
        route = Route(
            id='id1',
            responses=[r1, r2],
            response_selection=ResponseSelectionStrategy.random,
            path=re.compile(r'/test.*'),
            auth=NoAuth(),
            method='GET'
        )

        assert route.get_response('id1') is r1

    def test_get_response_not_found(self):
        r1 = RouteResponse('id1', 'string', Delay())
        route = Route(
            id='id1',
            responses=[r1],
            response_selection=ResponseSelectionStrategy.random,
            path=re.compile(r'/test.*'),
            auth=NoAuth(),
            method='GET'
        )

        assert route.get_response('id3') is None

    def test_use_increases_counter(self):
        response = RouteResponse('id1', 'string', Delay())
        route = Route(
            id='id1',
            responses=[response],
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
            responses=[],
            response_selection=ResponseSelectionStrategy.random,
            path=re.compile(r'/test.*'),
            auth=NoAuth(),
            method='GET'
        )

        route.use(None)
        assert route.used_count == 1

    def test_match_not_active(self):
        route = Route(
            id='id1',
            responses=[],
            response_selection=ResponseSelectionStrategy.random,
            path=re.compile(r'/test.*'),
            auth=NoAuth(),
            method='GET'
        )
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test_url',
            method='GET'
        )
        assert not route.match(request)

    def test_match_active(self):
        route = Route(
            id='id1',
            responses=[
                RouteResponse('id1', '', Delay(), weight=0.4)
            ],
            response_selection=ResponseSelectionStrategy.random,
            path=re.compile(r'/test.*'),
            auth=NoAuth(),
            method='GET'
        )
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test_url',
            method='GET'
        )
        assert route.match(request)

    def test_select_response(self):
        response = RouteResponse('id1', 'string', Delay())
        route = Route(
            id='id1',
            responses=[response],
            response_selection=ResponseSelectionStrategy.greedy,
            path=re.compile(r'/test.*'),
            auth=NoAuth(),
            method='GET'
        )

        assert route.select_response() is response

    def test_is_not_active_if_no_active_response(self):
        response = RouteResponse('id1', 'string', Delay(), repeat=0)
        route = Route(
            id='id1',
            responses=[response],
            response_selection=ResponseSelectionStrategy.greedy,
            path=re.compile(r'/test.*'),
            auth=NoAuth(),
            method='GET'
        )

        assert route.is_active == 0

    def test_authenticate(self):
        route = Route(
            id='id1',
            responses=[],
            response_selection=ResponseSelectionStrategy.random,
            path=re.compile(r'/test.*'),
            auth=NoAuth(),
            method='GET'
        )
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test_url',
            method='GET'
        )
        route.authenticate(request)


@pytest.mark.unit
class TestRouter:
    def test_initialize_empty_router(self):
        router = Router()
        assert list(router.routes) == []

    def test_add_route(self):
        router = Router()
        route = router.add_route({
            'id': 'id1',
            'path': '/endpoint_\\w*',
            'responses': [
                {
                    'id': 'response_1',
                    'body': {
                        'works': True
                    }
                }
            ]
        })

        assert list(router.routes) == [route]

    def test_add_duplicate_route_raises_exception(self):
        router = Router()
        route = router.add_route({
            'id': 'id1',
            'path': '/endpoint_\\w*',
            'responses': [
                {
                    'id': 'response_1',
                    'body': {
                        'works': True
                    }
                }
            ]
        })

        with pytest.raises(DuplicateRouteError):
            route = router.add_route({
                'id': 'id1',
                'path': '/endpoint_\\w*',
                'responses': [
                    {
                        'id': 'response_1',
                        'body': {
                            'works': True
                        }
                    }
                ]
            })

    def test_get_route(self):
        router = Router()
        route = router.add_route({
            'id': 'id1',
            'path': '/endpoint_\\w*',
            'responses': [
                {
                    'id': 'response_1',
                    'body': {
                        'works': True
                    }
                }
            ]
        })

        assert router.get_route('id1') is route

    def test_get_route(self):
        router = Router()
        assert router.get_route('id1') is None

    def test_remove_route(self):
        router = Router()
        route = router.add_route({
            'id': 'id1',
            'path': '/endpoint_\\w*',
            'responses': [
                {
                    'id': 'response_1',
                    'body': {
                        'works': True
                    }
                }
            ]
        })
        router.remove_route('id1')
        
        assert list(router.routes) == []

    def test_match_route(self):
        router = Router()
        route = router.add_route({
            'id': 'id1',
            'path': '/endpoint\\w*',
            'responses': [
                {
                    'id': 'response_1',
                    'body': {
                        'works': True
                    }
                }
            ]
        })
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/endpoint',
            method='GET'
        )
        
        assert router.match(request) is route

    def test_match_with_no_matching_route(self):
        router = Router()
        route = router.add_route({
            'id': 'id1',
            'path': '/endpoint\\w*',
            'responses': [
                {
                    'id': 'response_1',
                    'body': {
                        'works': True
                    }
                }
            ]
        })
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET'
        )
        
        assert router.match(request) is None

    def test_update_route_not_present(self):
        router = Router()

        with pytest.raises(MissingRouteError):
            router.update_route({
                'id': 'id1',
                'path': '/endpoint\\w*',
                'responses': [
                    {
                        'id': 'response_1',
                        'body': {
                            'works': True
                        }
                    }
                ]
            }, 'id1')

    def test_update_route_to_that_already_exists(self):
        router = Router()
        router.add_route({
            'id': 'id1',
            'path': '/endpoint\\w*',
            'responses': [
                {
                    'id': 'response_1',
                    'body': {
                        'works': True
                    }
                }
            ]
        })

        router.add_route({
            'id': 'id2',
            'path': '/endpoint\\w*',
            'responses': [
                {
                    'id': 'response_2',
                    'body': {
                        'works': True
                    }
                }
            ]
        })

        with pytest.raises(DuplicateRouteError):
            router.update_route({
                'id': 'id1',
                'path': '/endpoint\\w*',
                'responses': [
                    {
                        'id': 'response_1',
                        'body': {
                            'works': True
                        }
                    }
                ]
            }, 'id2')

    def test_update_route_and_change_its_id(self):
        router = Router()
        router.add_route({
            'id': 'id1',
            'path': '/endpoint\\w*',
            'responses': [
                {
                    'id': 'response_1',
                    'body': {
                        'works': True
                    }
                }
            ]
        })

        router.update_route({
            'id': 'id2',
            'path': '/endpoint\\w*',
            'responses': [
                {
                    'id': 'response_1',
                    'body': {
                        'works': True
                    }
                }
            ]
        }, 'id1')

    def test_reset_router_with_default_routes(self):
        router = Router()
        router.reset([
            {
                "path": "/minimal_endpoint",
                "responses": [
                    {
                        "body": "response"
                    }
                ]
            }
        ])
        
        assert len(router.routes) == 1
