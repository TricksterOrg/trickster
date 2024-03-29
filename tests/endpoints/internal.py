import copy
import http
import uuid

from trickster.model import Route, Response, ResponseValidator
from tests.conftest import AUTH_TOKEN


class TestHealthcheck:
    def test_healthcheck(self, mocked_config, client):
        result = client.get(f'{mocked_config.internal_prefix}/healthcheck')

        assert result.status_code == 200
        assert result.json() == {'status': 'OK'}


class TestInternalEndpoints:
    payload_route = {
        'path': '/items',
        'responses': [
            {
                'status_code': http.HTTPStatus.OK, 'body': {'user_id': 1234, 'user_name': 'Mark Twain'}
            }
        ],
        'http_methods': [http.HTTPMethod.POST],
        'response_validators': [
            {
                'status_code': http.HTTPStatus.OK,
                'json_schema': {
                    '$schema': 'https://json-schema.org/draft/2020-12/schema',
                    'required': ['user_id'],
                    'properties': {'user_id': {'type': 'number'}, 'user_name': {'type': 'string'}}
                }
            }
        ]
    }

    payload_response_validator = {
        'status_code': http.HTTPStatus.OK,
        'json_schema': {
            '$schema': 'https://json-schema.org/draft/2020-12/schema',
            'properties': {'book_id': {'type': 'number'}, 'book_name': {'type': 'string'}}
        }
    }

    payload_error_response = {'status_code': http.HTTPStatus.FORBIDDEN, 'body': {'detail': 'It is forbidden.'}}

    def test_get_routes(self, mocked_config, mocked_router, client):
        expected_routes = [{
            'id': str(mocked_router.routes[0].id),
            'auth': {
                'method': 'token',
                'token': AUTH_TOKEN,
                'error_response': {
                    'id': str(mocked_router.routes[0].auth.error_response.id),
                    'body': {'auth': 'unauthorized'},
                    'delay': [0.0, 0.0],
                    'headers': {},
                    'hits': 0,
                    'status_code': 401,
                    'weight': 1.0,
                }
            },
            'hits': 0,
            'response_selector': 'first',
            'http_methods': ['GET'],
            'path': '/users',
            'response_validators': [
                {
                    'id': str(mocked_router.routes[0].response_validators[0].id),
                    'status_code': 200,
                    'json_schema': {
                        '$schema': 'https://json-schema.org/draft/2020-12/schema',
                        'required': ['user_id'],
                        'properties': {'user_id': {'type': 'number'}, 'user_name': {'type': 'string'}}
                    }
                }
            ],
            'responses': [
                {
                    'id': str(mocked_router.routes[0].responses[0].id),
                    'body': {'user_id': 1234, 'user_name': 'Mark Twain'},
                    'delay': [0.0, 0.0],
                    'headers': {},
                    'hits': 0,
                    'status_code': 200,
                    'weight': 1.0
                }, {
                    'id': str(mocked_router.routes[0].responses[1].id),
                    'body': {'user_id': 5678, 'user_name': 'Charles Dickens'},
                    'delay': [0.0, 0.0],
                    'headers': {},
                    'hits': 0,
                    'status_code': 200,
                    'weight': 1.0
                }
            ]
        }]

        result = client.get(
            f'{mocked_config.internal_prefix}/routes', headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 200
        assert result.json() == expected_routes

    def test_get_route(self, mocked_config, mocked_router, client):
        route_id = mocked_router.routes[0].id

        result = client.get(
            f'{mocked_config.internal_prefix}/routes/{route_id}', headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 200
        assert result.json()['id'] == str(mocked_router.routes[0].id)

    def test_get_route_non_existent(self, mocked_config, client):
        non_existent_id = uuid.uuid4()
        result = client.get(
            f'{mocked_config.internal_prefix}/routes/{non_existent_id}',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 404
        assert result.json() == {'error': 'Resource error', 'reason': f'Route ID "{non_existent_id}" was not found.'}

    def test_create_route(self, mocked_router_empty, mocked_config, client):
        result = client.post(
            f'{mocked_config.internal_prefix}/routes', json=self.payload_route,
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == http.HTTPStatus.OK
        assert result.json()['id'] == str(mocked_router_empty.routes[0].id)

    def test_create_route_invalid(self, mocked_router_empty, mocked_config, client):
        route = copy.deepcopy(self.payload_route)
        additional_response_invalid = {'status_code': http.HTTPStatus.OK, 'body': {'user_name': 'Arthur Clarke'}}
        route['responses'].append(additional_response_invalid)

        result = client.post(
            f'{mocked_config.internal_prefix}/routes', json=route,
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 400
        assert result.json()['error'] == 'Validation error'

    def test_delete_routes(self, mocked_config, mocked_router, client):
        result = client.delete(
            f'{mocked_config.internal_prefix}/routes', headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 200
        assert result.json() == []

    def test_delete_route(self, mocked_config, mocked_router, client):
        additional_payload = {
            'path': '/books',
            'responses': [
                {'status_code': http.HTTPStatus.OK, 'body': {'book_id': 3434, 'book_name': '16 Short Novels'}}
            ],
            'http_method': http.HTTPMethod.POST,
            'response_validators': [
                {
                    'status_code': http.HTTPStatus.OK,
                    'json_schema': {
                        '$schema': 'https://json-schema.org/draft/2020-12/schema',
                        'properties': {'body': {'type': 'object'}}
                    }
                }
            ]
        }
        mocked_router.add_route(Route(**additional_payload))
        route_id = mocked_router.routes[0].id

        result = client.delete(
            f'{mocked_config.internal_prefix}/routes/{route_id}', headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )
        result_body = result.json()

        assert result.status_code == http.HTTPStatus.OK

        assert len(result_body) != 0
        assert route_id not in [i['id'] for i in result_body]

    def test_delete_route_non_existent(self, mocked_config, client):
        non_existent_id = uuid.uuid4()
        result = client.delete(
            f'{mocked_config.internal_prefix}/routes/{non_existent_id}',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 404
        assert result.json() == {'error': 'Resource error', 'reason': f'Route "{non_existent_id}" was not found.'}

    def test_get_route_responses(self, mocked_router, mocked_config, client):
        route_id = mocked_router.routes[0].id

        result = client.get(
            f'{mocked_config.internal_prefix}/routes/{route_id}/responses',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )
        result_body = result.json()

        assert result.status_code == 200
        assert result_body[0]['id'] == str(mocked_router.routes[0].responses[0].id)
        assert result_body[0]['body'] == mocked_router.routes[0].responses[0].body
        assert result_body[0]['status_code'] == mocked_router.routes[0].responses[0].status_code

    def test_get_route_responses_non_existent(self, mocked_config, client):
        non_existent_id = uuid.uuid4()
        result = client.get(
            f'{mocked_config.internal_prefix}/routes/{non_existent_id}/responses',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 404
        assert result.json() == {'error': 'Resource error', 'reason': f'Route "{non_existent_id}" was not found.'}

    def test_delete_route_response(self, mocked_config, mocked_router, client):
        route_id = str(mocked_router.routes[0].id)
        response_id = str(mocked_router.routes[0].responses[0].id)

        result = client.delete(
            f'{mocked_config.internal_prefix}/routes/{route_id}/responses/{response_id}',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )
        result_body = result.json()

        assert result.status_code == 200

        assert len(result_body) != 0
        assert response_id not in [i['id'] for i in result_body['responses']]

    def test_delete_route_response_non_existent(self, mocked_config, mocked_router, client):
        route_id = str(mocked_router.routes[0].id)
        response_id = str(mocked_router.routes[0].responses[0].id)
        non_existent_id = uuid.uuid4()

        result = client.delete(
            f'{mocked_config.internal_prefix}/routes/{non_existent_id}/responses/{response_id}',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 404
        assert result.json() == {'error': 'Resource error', 'reason': f'Route "{non_existent_id}" was not found.'}

        result = client.delete(f'{mocked_config.internal_prefix}/routes/{route_id}/responses/{non_existent_id}')

        assert result.status_code == 404
        assert result.json() == {'error': 'Resource error', 'reason': f'Response "{non_existent_id}" was not found in route "{route_id}".'}

    def test_delete_route_responses(self, mocked_config, mocked_router, client):
        route_id = mocked_router.routes[0].id

        result = client.delete(
            f'internal/routes/{route_id}/responses',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 200

        assert result.json()['responses'] == []

    def test_delete_route_responses_non_existent(self, mocked_config, client):
        non_existent_id = uuid.uuid4()
        result = client.delete(
            f'{mocked_config.internal_prefix}/routes/{non_existent_id}/responses',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 404
        assert result.json() == {'error': 'Resource error', 'reason': f'Route "{non_existent_id}" was not found.'}

    def test_create_route_response(self, mocked_router, mocked_config, client):
        route_id = mocked_router.routes[0].id
        new_response = {'status_code': http.HTTPStatus.OK, 'body': {'user_id': 6767, 'some': 'field'}}

        result = client.post(
            f'{mocked_config.internal_prefix}/routes/{route_id}/responses',
            json=new_response,
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )
        result_body = result.json()

        assert result.status_code == 200
        assert result_body['responses'][2]['body'] == new_response['body']
        assert result_body['responses'][2]['status_code'] == new_response['status_code']

    def test_create_route_response_non_existent(self, mocked_config, client):
        non_existent_id = uuid.uuid4()
        new_response = {'status_code': http.HTTPStatus.OK, 'body': {'user_id': 6767, 'some': 'field'}}

        result = client.post(
            f'{mocked_config.internal_prefix}/routes/{non_existent_id}/responses',
            json=new_response,
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 404
        assert result.json() == {'error': 'Resource error', 'reason': f'Route "{non_existent_id}" was not found.'}

    def test_get_route_response_validators(self, mocked_router, mocked_config, client):
        mocked_router.routes[0].response_validators.append(ResponseValidator(**self.payload_response_validator))
        route_id = mocked_router.routes[0].id

        result = client.get(
            f'internal/routes/{route_id}/response_validators', headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )
        result_body = result.json()

        assert result.status_code == 200
        assert len(result_body) == 2
        assert result_body[0]['json_schema'] == mocked_router.routes[0].response_validators[0].json_schema
        assert result_body[0]['status_code'] == mocked_router.routes[0].response_validators[0].status_code
        assert result_body[1]['json_schema'] == mocked_router.routes[0].response_validators[1].json_schema
        assert result_body[1]['status_code'] == mocked_router.routes[0].response_validators[1].status_code

    def test_get_route_response_validators_non_existent_route(self, mocked_config, client):
        non_existent_id = uuid.uuid4()
        result = client.get(
            f'{mocked_config.internal_prefix}/routes/{non_existent_id}/response_validators',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 404
        assert result.json() == {'error': 'Resource error', 'reason': f'Route "{non_existent_id}" was not found.'}

    def test_delete_route_response_validator(self, mocked_router, mocked_config, client):
        mocked_router.routes[0].response_validators.append(ResponseValidator(**self.payload_response_validator))
        route_id = mocked_router.routes[0].id
        response_validator_id = mocked_router.routes[0].response_validators[0].id

        result = client.delete(
            f'{mocked_config.internal_prefix}/routes/{route_id}/response_validators/{response_validator_id}',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )
        result_body = result.json()

        assert result.status_code == 200
        assert len(result_body['response_validators']) == 1
        assert route_id not in [i['id'] for i in result_body['response_validators']]

    def test_delete_route_response_validator_non_existent(self, mocked_router, mocked_config, client):
        non_existent_id = uuid.uuid4()
        route_id = mocked_router.routes[0].id
        response_validator_id = mocked_router.routes[0].response_validators[0].id
        result = client.delete(
            f'{mocked_config.internal_prefix}/routes/{route_id}/response_validators/{non_existent_id}',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 404
        assert result.json() == {
            'error': 'Resource error',
            'reason': f'Response_validator "{non_existent_id}" was not found in route "{route_id}".'
        }

        result = client.delete(
            f'{mocked_config.internal_prefix}/routes/{non_existent_id}/response_validators/{response_validator_id}',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 404
        assert result.json() == {'error': 'Resource error', 'reason': f'Route "{non_existent_id}" was not found.'}

    def test_delete_route_response_validators(self, mocked_router, mocked_config, client):
        route_id = mocked_router.routes[0].id

        result = client.delete(
            f'{mocked_config.internal_prefix}/routes/{route_id}/response_validators',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 200
        assert result.json()['response_validators'] == []

    def test_delete_route_response_validators_non_existent(self, mocked_config, client):
        non_existent_id = uuid.uuid4()
        result = client.delete(
            f'{mocked_config.internal_prefix}/routes/{non_existent_id}/response_validators',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 404
        assert result.json() == {'error': 'Resource error', 'reason': f'Route "{non_existent_id}" was not found.'}

    def test_create_route_response_validator(self, mocked_router, mocked_config, client):
        route_id = mocked_router.routes[0].id

        result = client.post(
            f'{mocked_config.internal_prefix}/routes/{route_id}/response_validators',
            json=self.payload_response_validator,
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )
        result_body = result.json()

        assert result.status_code == 200
        assert result_body['response_validators'][1]['json_schema'] == self.payload_response_validator['json_schema']
        assert result_body['response_validators'][1]['status_code'] == self.payload_response_validator['status_code']

    def test_create_route_response_validator_non_existent(self, mocked_config, client):
        non_existent_id = uuid.uuid4()
        result = client.post(
            f'{mocked_config.internal_prefix}/routes/{non_existent_id}/response_validators',
            json=self.payload_response_validator,
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 404
        assert result.json() == {'error': 'Resource error', 'reason': f'Route "{non_existent_id}" was not found.'}

    def test_get_error_responses(self, mocked_router, mocked_config, client):
        expected_error_responses = [(i.status_code, i.body) for i in mocked_config.settings.error_responses] + \
                                   [(self.payload_error_response['status_code'], self.payload_error_response['body'])]
        mocked_router.add_error_response(Response(**self.payload_error_response))

        result = client.get(
            f'{mocked_config.internal_prefix}/settings/error_responses',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 200
        assert [(i['status_code'], i['body']) for i in result.json()] == expected_error_responses

    def test_create_error_response(self, mocked_router, mocked_config, client):
        result = client.post(
            f'{mocked_config.internal_prefix}/settings/error_responses',
            json=self.payload_error_response,
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )
        result_body = result.json()

        assert result.status_code == 200
        assert result_body['body'] == self.payload_error_response['body']
        assert result_body['status_code'] == self.payload_error_response['status_code']

    def test_delete_error_responses(self, mocked_router, mocked_config, client):
        result = client.delete(
            f'{mocked_config.internal_prefix}/settings/error_responses',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 200
        assert result.json() == []

    def test_delete_error_response(self, mocked_router, mocked_config, client):
        mocked_router.add_error_response(Response(**self.payload_error_response))
        error_response_id = mocked_router.error_responses[-1].id

        result = client.delete(
            f'{mocked_config.internal_prefix}/settings/error_responses/{error_response_id}',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 200
        assert error_response_id not in [i['id'] for i in result.json()]

    def test_delete_error_response_non_existent(self, mocked_config, client):
        non_existent_id = uuid.uuid4()
        result = client.delete(
            f'{mocked_config.internal_prefix}/settings/error_responses/{non_existent_id}',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 404
        assert result.json() == {
            'error': 'Resource error', 'reason': f'Error response "{non_existent_id}" was not found.'
        }

    def test_get_non_existent_internal_endpoint(self, mocked_router, mocked_config, client):
        result = client.get(
            f'{mocked_config.internal_prefix}/non-existent-path',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
        )

        assert result.status_code == 404
