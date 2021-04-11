"""Integration tests of API endpoints.

Attributes of objects should be defined in this order:

# Route
id
path
method
response_selection
used_count
is_active
auth
responses


# Response 
id
status
repeat
weight
used_count
is_active
delay
headers
body
"""


import pytest
from pathlib import Path


@pytest.mark.integration
class TestApi:
    def test_get_empty_routes(self, client):
        response = client.get('/internal/routes')
        assert response.json == []

    def test_add_minimal_route(self, client):
        response = client.post('/internal/routes', json={
            'id': 'route_id',
            'path': '/path',
            'responses': [
                {
                    'id': 'response_id',
                    'body': 'response_body'
                }
            ]
        })

        assert response.status_code == 201
        assert response.json == {
            'id': 'route_id',
            'path': '/path',
            'method': 'GET',
            'response_selection': 'greedy',
            'used_count': 0,
            'is_active': True,
            'auth': None,
            'responses': [
                {
                    'id': 'response_id',
                    'status': 200,
                    'repeat': None,
                    'weight': 0.5,
                    'used_count': 0,
                    'is_active': True,
                    'delay': 0.0,
                    'headers': {},
                    'body': 'response_body'
                }
            ]
        }

    def test_add_full_route(self, client):
        response = client.post('/internal/routes', json={
            'id': 'route_id',
            'path': '/endpoint',
            'method': 'GET',
            'response_selection': 'random',
            'auth': {
                'method': 'basic',
                'username': 'username',
                'password': 'password'
            },
            'responses': [
                {
                    'id': 'response_id1',
                    'status': 200,
                    'repeat': 3,
                    'weight': 0.3,
                    'delay': 0.5,
                    'headers': {
                        'content-type': 'application/json'
                    },
                    'body': {
                        'content': "response_body1"
                    }
                },
                {
                    'id': 'response_id2',
                    'status': 500,
                    'repeat': 3,
                    'weight': 0.1,
                    'delay': [0.1, 0.2],
                    'headers': {
                        'content-type': 'application/json'
                    },
                    'body': {
                        'content': "response_body2"
                    }
                }
            ]
        })

        assert response.status_code == 201
        assert response.json == {
            'id': 'route_id',
            'path': '/endpoint',
            'method': 'GET',
            'response_selection': 'random',
            'used_count': 0,
            'is_active': True,
            'auth': {
                'method': 'basic',
                'password': 'password',
                'username': 'username',
                'unauthorized_response': {
                    'body': {
                        'error': 'Unauthorized',
                        'message': 'Authentication failed.'
                    },
                    'delay': 0.0,
                    'headers': {},
                    'status': 401,
                    'used_count': 0
                }
            },
            'responses': [
                {
                    'id': 'response_id1',
                    'status': 200,
                    'repeat': 3,
                    'weight': 0.3,
                    'is_active': True,
                    'used_count': 0,
                    'delay': 0.5,
                    'headers': {
                        'content-type': 'application/json'
                    },
                    'body': {
                        'content': "response_body1"
                    }
                },
                {
                    'id': 'response_id2',
                    'status': 500,
                    'repeat': 3,
                    'weight': 0.1,
                    'used_count': 0,
                    'is_active': True,
                    'delay': [0.1, 0.2],
                    'headers': {
                        'content-type': 'application/json'
                    },
                    'body': {
                        'content': "response_body2"
                    }
                }
            ]
        }


    def test_append_route(self, client):
        client.post('/internal/routes', json={
            'id': 'route_id1',
            'path': '/endpoint1',
            'responses': [
                {
                    'id': 'response_id1',
                    'body': 'response_body1'
                }
            ]
        })

        client.post('/internal/routes', json={
            'id': 'route_id2',
            'path': '/endpoint2',
            'responses': [
                {
                    'id': 'response_id2',
                    'body': 'response_body2'
                }
            ]
        })

        response = client.get('/internal/routes')
        assert response.status_code == 200
        assert response.json == [
            {
                'id': 'route_id1',
                'path': '/endpoint1',
                'method': 'GET',
                'response_selection': 'greedy',
                'used_count': 0,
                'is_active': True,
                'auth': None,
                'responses': [
                    {
                        'id': 'response_id1',
                        'status': 200,
                        'repeat': None,
                        'weight': 0.5,
                        'used_count': 0,
                        'is_active': True,
                        'delay': 0.0,
                        'headers': {},
                        'body': 'response_body1'
                    }
                ]
            },
            {
                'id': 'route_id2',
                'path': '/endpoint2',
                'method': 'GET',
                'response_selection': 'greedy',
                'used_count': 0,
                'is_active': True,
                'auth': None,
                'responses': [
                    {
                        'id': 'response_id2',
                        'status': 200,
                        'repeat': None,
                        'weight': 0.5,
                        'used_count': 0,
                        'is_active': True,
                        'delay': 0.0,
                        'headers': {},
                        'body': 'response_body2'
                    }
                ]
            }
        ]

    def test_reset_routes(self, client):
        client.post('/internal/route', json={
            'id': 'route1',
            'path': '/endpoint1',
            'responses': [
                {
                    'id': 'response1',
                    'body': 'response1'
                }
            ]
        })

        client.delete('/internal/routes')
        response = client.get('/internal/routes')
        assert response.status_code == 200
        assert response.json == []


    def test_create_and_delete_route(self, client):
        client.post('/internal/routes', json={
            'id': 'route1',
            'path': '/endpoint1',
            'responses': [
                {
                    'id': 'response1',
                    'body': 'response1'
                }
            ]
        })

        response = client.delete('/internal/routes/route1')
        assert response.status_code == 204
        
        response = client.get('/internal/routes')
        assert response.status_code == 200
        assert response.json == []


    def test_update_route(self, client):
        client.post('/internal/routes', json={
            'id': 'route1',
            'path': '/endpoint1',
            'responses': [
                {
                    'body': 'response1'
                }
            ]
        })

        response = client.put('/internal/routes/route1', json={
            'path': '/endpoint2',
            'responses': [
                {
                    'id': 'response2',
                    'body': 'response2'
                }
            ]
        })
        assert response.status_code == 201

        response = client.get('/internal/routes')
        assert response.status_code == 200
        assert response.json == [{
            'auth': None,
            'id': 'route1',
            'method': 'GET',
            'path': '/endpoint2',
            'response_selection': 'greedy',
            'responses': [
                {
                    'body': 'response2',
                    'delay': 0.0,
                    'headers': {},
                    'id': 'response2',
                    'is_active': True,
                    'repeat': None,
                    'status': 200,
                    'used_count': 0,
                    'weight': 0.5
                }
            ],
            'used_count': 0,
            'is_active': True
        }]

    def test_update_route_change_route_id(self, client):
        client.post('/internal/routes', json={
            'id': 'route1',
            'path': '/endpoint1',
            'responses': [
                {
                    'body': 'response1'
                }
            ]
        })

        response = client.put('/internal/routes/route1', json={
            'id': 'route2',
            'path': '/endpoint2',
            'responses': [
                {
                    'id': 'response2',
                    'body': 'response2'
                }
            ]
        })
        assert response.status_code == 201

        response = client.get('/internal/routes')
        assert response.status_code == 200
        assert response.json == [{
            'auth': None,
            'id': 'route2',
            'method': 'GET',
            'path': '/endpoint2',
            'response_selection': 'greedy',
            'responses': [
                {
                    'body': 'response2',
                    'delay': 0.0,
                    'headers': {},
                    'id': 'response2',
                    'is_active': True,
                    'repeat': None,
                    'status': 200,
                    'used_count': 0,
                    'weight': 0.5
                }
            ],
            'used_count': 0,
            'is_active': True
        }]


    def test_update_route_change_route_id_to_another_that_exists(self, client):
        client.post('/internal/routes', json={
            'id': 'route1',
            'path': '/endpoint1',
            'responses': [
                {
                    'body': 'response1'
                }
            ]
        })
        client.post('/internal/routes', json={
            'id': 'route2',
            'path': '/endpoint2',
            'responses': [
                {
                    'body': 'response2'
                }
            ]
        })
        response = client.put('/internal/routes/route1', json={
            'id': 'route2',
            'path': '/endpoint2',
            'responses': [
                {
                    'id': 'response2',
                    'body': 'response2'
                }
            ]
        })

        assert response.status_code == 409
        assert response.json == {
            'error': 'Conflict',
            'message': 'Cannot change route id "route1" to "route2". Route id "route2" already exists.'
        }

    def test_update_route_that_doesnt_exist(self, client):
        response = client.put('/internal/routes/route1', json={
            'id': 'route2',
            'path': '/endpoint2',
            'responses': [
                {
                    'id': 'response2',
                    'body': 'response2'
                }
            ]
        })

        assert response.status_code == 404
        assert response.json == {
            'error': 'Not Found',
            'message': 'Cannot update route "route1". Route doesn\'t exist.'
        }

    def test_append_duplicate_route(self, client):
        client.post('/internal/routes', json={
            'id': 'route1',
            'path': '/endpoint1',
            'responses': [
                {
                    'id': 'response1',
                    'body': 'response1'
                }
            ]
        })

        response = client.post('/internal/routes', json={
            'id': 'route1',
            'path': '/endpoint2',
            'responses': [
                {
                    'id': 'response2',
                    'body': 'response2'
                }
            ]
        })

        assert response.status_code == 409
        assert response.json == {
            'error': 'Conflict',
            'message': 'Route id "route1" already exists.'
        }

    def test_call_route(self, client):
        client.post('/internal/routes', json={
            'id': 'route',
            'path': '/endpoint',
            'responses': [
                {
                    'id': 'response',
                    'body': {'response': 'data'}
                }
            ]
        })

        response = client.get('/endpoint')

        assert response.status_code == 200
        assert response.json == {'response': 'data'}

    def test_call_route_no_match(self, client):
        response = client.get('/endpoint')

        assert response.status_code == 404
        assert response.json == {
            'error': 'Not Found',
            'message': 'The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.'
        }

    def test_call_one_route_from_multiple(self, client):
        client.post('/internal/routes', json={
            'path': '/endpoint1',
            'responses': [
                {
                    'id': 'response',
                    'body': {'response': 'data1'}
                }
            ]
        })
        client.post('/internal/routes', json={
            'path': '/endpoint2',
            'responses': [
                {
                    'id': 'response',
                    'body': {'response': 'data2'}
                }
            ]
        })

        response = client.get('/endpoint2')
        assert response.status_code == 200
        assert response.json == {'response': 'data2'}

    def test_route_doesnt_match_when_it_runs_out_of_responses(self, client):
        client.post('/internal/routes', json={
            'path': '/endpoint',
            'responses': [
                {
                    'repeat': 1,
                    'body': {'response': 'data1'}
                }
            ]
        })
        client.post('/internal/routes', json={
            'path': '/endpoint',
            'responses': [
                {
                    'id': 'response',
                    'body': {'response': 'data2'}
                }
            ]
        })

        response = client.get('/endpoint')
        assert response.status_code == 200
        assert response.json == {'response': 'data1'}

        response = client.get('/endpoint')
        assert response.status_code == 200
        assert response.json == {'response': 'data2'}

    def test_get_route(self, client):
        client.post('/internal/routes', json={
            'id': 'route_id',
            'path': '/endpoint',
            'responses': [
                {
                    'id': 'response_id',
                    'body': 'response'
                }
            ]
        })

        response = client.get('/internal/routes/route_id')
        assert response.status_code == 200
        assert response.json == {
            'auth': None,
            'id': 'route_id',
            'method': 'GET',
            'path': '/endpoint',
            'response_selection': 'greedy',
            'responses': [
                {
                    'body': 'response',
                    'delay': 0.0,
                    'headers': {},
                    'id': 'response_id',
                    'is_active': True,
                    'repeat': None,
                    'status': 200,
                    'used_count': 0,
                    'weight': 0.5
                }
            ],
            'used_count': 0,
            'is_active': True
        }

    def test_get_route_not_found(self, client):
        response = client.get('/internal/routes/route_id')
        assert response.status_code == 404
        assert response.json == {
            'error': 'Not Found',
            'message': 'Route id "route_id" does not exist.'
        }

    def test_get_responses(self, client):
        client.post('/internal/routes', json={
            'id': 'route_id',
            'path': '/endpoint',
            'responses': [
                {
                    'id': 'response_id1',
                    'body': 'response1'
                },
                {
                    'id': 'response_id2',
                    'body': 'response2'
                }
            ]
        })

        response = client.get('/internal/routes/route_id/responses')
        assert response.status_code == 200
        assert response.json == [
            {
                'body': 'response1',
                'delay': 0.0,
                'headers': {},
                'id': 'response_id1',
                'is_active': True,
                'repeat': None,
                'status': 200,
                'used_count': 0,
                'weight': 0.5
            },
            {
                'body': 'response2',
                'delay': 0.0,
                'headers': {},
                'id': 'response_id2',
                'is_active': True,
                'repeat': None,
                'status': 200,
                'used_count': 0,
                'weight': 0.5
            }
        ]

    def test_get_responses_route_not_found(self, client):
        response = client.get('/internal/routes/route_id/responses')
        assert response.status_code == 404
        assert response.json == {
            'error': 'Not Found',
            'message': 'Route id "route_id" does not exist.'
        }

    def test_get_response(self, client):
        client.post('/internal/routes', json={
            'id': 'route_id',
            'path': '/endpoint',
            'responses': [
                {
                    'id': 'response_id1',
                    'body': 'response1'
                }
            ]
        })

        response = client.get('/internal/routes/route_id/responses/response_id1')
        assert response.status_code == 200
        assert response.json == {
            'body': 'response1',
            'delay': 0.0,
            'headers': {},
            'id': 'response_id1',
            'is_active': True,
            'repeat': None,
            'status': 200,
            'used_count': 0,
            'weight': 0.5
        }

    def test_get_response_not_found(self, client):
        client.post('/internal/routes', json={
            'id': 'route_id',
            'path': '/endpoint',
            'responses': []
        })

        response = client.get('/internal/routes/route_id/responses/response_id')
        assert response.status_code == 404
        assert response.json == {
            'error': 'Not Found',
            'message': 'Response id "response_id" does not exist in request id "route_id".'
        }

    def test_get_response_route_not_found(self, client):
        response = client.get('/internal/routes/route_id/responses/response_id')
        assert response.status_code == 404
        assert response.json == {
            'error': 'Not Found',
            'message': 'Route id "route_id" does not exist.'
        }

    def test_remove_route(self, client):
        client.post('/internal/routes', json={
            'id': 'route_id',
            'path': '/path',
            'responses': [
                {
                    'id': 'response_id',
                    'body': 'response_body'
                }
            ]
        })

        client.delete('/internal/routes/route_id')
        response = client.get('/internal/routes')
        assert response.json == []

    def test_remove_route_that_doesnt_exist(self, client):
        response = client.delete('/internal/routes/route_id')
        assert response.status_code == 404
        assert response.json == {
            'error': 'Not Found',
            'message': 'Route id "route_id" does not exist.'
        }

    def test_match_route(self, client):
        client.post('/internal/routes', json={
            'id': 'route_id',
            'path': '/path',
            'responses': [
                {
                    'id': 'response_id',
                    'body': 'response_body'
                }
            ]
        })

        response = client.post('/internal/match_route', json={
            'method': 'GET',
            'path': '/path',
        })

        assert response.status_code == 200
        assert response.json == {
            'id': 'route_id',
            'path': '/path',
            'method': 'GET',
            'response_selection': 'greedy',
            'used_count': 0,
            'is_active': True,
            'auth': None,
            'responses': [
                {
                    'id': 'response_id',
                    'status': 200,
                    'repeat': None,
                    'weight': 0.5,
                    'used_count': 0,
                    'is_active': True,
                    'delay': 0.0,
                    'headers': {},
                    'body': 'response_body'
                }
            ]
        }


    def test_match_route_not_found(self, client):
        response = client.post('/internal/match_route', json={
            'method': 'GET',
            'path': '/path',
        })

        assert response.status_code == 404
        assert response.json == {
            'error': 'Not Found',
            'message': 'No route was matched.'
        }

    def test_call_route_authentication_error(self, client):
        response = client.post('/internal/routes', json={
            'id': 'route_id',
            'path': '/path',
            'auth': {
                'method': 'hmac',
                'key': 'secret_key'
            },
            'responses': [
                {
                    'id': 'response_id',
                    'body': 'response_body'
                }
            ]
        })

        response = client.get('/path', json={
            'method': 'GET',
            'path': '/path',
        })

        assert response.status_code == 401
        assert response.json == {
            'error': 'Unauthorized',
            'message': 'HMAC authentication failed, URL is missing required parameter: "hmac_timestamp".'
        }
