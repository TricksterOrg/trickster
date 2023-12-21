import http
import uuid
import copy


class TestHealthcheck:
    def test_healthcheck(self, client):
        response = client.get('/internal/healthcheck')

        assert response.status_code == 200
        assert response.json() == {'status': 'OK'}


class TestInternalEndpoints:
    payload_route = {
        'id': 'ae2f774d-25bd-416e-b6e5-35c8892b5db4',
        'hits': 1,
        'path': '/users',
        'responses': [
            {
                'id': '9566b682-3531-49aa-ab11-724d3cb3b5fd',
                'status_code': http.HTTPStatus.OK, 'body': {'user_id': 1234, 'user_name': 'Mark Twain'}
            },
            {
                'id': '7777b682-3531-49aa-ab11-724d3cb3baaa',
                'status_code': http.HTTPStatus.OK, 'body': {'user_id': 5678, 'user_name': 'Charles Dickens'}
            }
        ],
        'http_method': http.HTTPMethod.POST,
        'response_validators': [
            {
                'status_code': http.HTTPStatus.OK,
                'json_schema': {
                    '$schema': 'https://json-schema.org/draft/2020-12/schema',
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

    payload_error_response = {'status_code': http.HTTPStatus.NOT_FOUND, 'body': {'detail': 'Did not found'}}

    def test_get_routes(self, client):
        client.post('/internal/routes', json=self.payload_route)

        response = client.get('/internal/routes')

        assert response.status_code == 200

        response_body = response.json()
        expected_body = copy.deepcopy(self.payload_route)

        # assert response_body == [expected_body]

    def test_get_route(self, client):
        response = client.post('/internal/routes', json=self.payload_route)
        response_id = response.json()['id']

        response = client.get(f'/internal/routes/{response_id}')
        assert response.status_code == 200
        assert response.json()['id'] == response_id

        non_existent_id = uuid.uuid4()
        response = client.get(f'/internal/routes/{non_existent_id}')

        assert response.status_code == 404
        assert response.json() == {'detail': f'Route ID "{non_existent_id}" was not found.'}

    def test_create_route(self, client):
        response = client.post('/internal/routes', json=self.payload_route)

        assert response.status_code == http.HTTPStatus.OK

        stored_route = client.get(f'/internal/routes/{response.json()["id"]}')
        assert response.json()['id'] == stored_route.json()['id']

    def test_delete_routes(self, client):
        client.post('/internal/routes', json=self.payload_route)

        response = client.delete('/internal/routes')

        assert response.status_code == 200
        assert response.json() == []

    def test_delete_route(self, client):
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
        response = client.post('/internal/routes', json=self.payload_route)
        route_id = response.json()['id']
        client.post('/internal/routes', json=additional_payload)

        response = client.delete(f'/internal/routes/{route_id}')

        assert response.status_code == http.HTTPStatus.OK
        assert route_id not in [i['id'] for i in response.json()]

        non_existent_id = uuid.uuid4()
        response = client.delete(f'/internal/routes/{non_existent_id}')

        assert response.status_code == 404
        assert response.json() == {'detail': f'Route "{non_existent_id}" was not found.'}

    def test_get_route_responses(self, client):
        response = client.post('/internal/routes', json=self.payload_route)
        route_id = response.json()['id']

        response = client.get(f'/internal/routes/{route_id}/responses')
        assert response.status_code == 200
        assert response.json()[0]['body'] == self.payload_route['responses'][0]['body']
        assert response.json()[0]['status_code'] == self.payload_route['responses'][0]['status_code']

        non_existent_id = uuid.uuid4()
        response = client.get(f'/internal/routes/{non_existent_id}/responses')

        assert response.status_code == 404
        assert response.json() == {'detail': f'Route "{non_existent_id}" was not found.'}

    def test_delete_route_response(self, client):
        response = client.post('/internal/routes', json=self.payload_route)
        route_id = response.json()['id']
        response_id = response.json()['responses'][0]['id']

        response = client.delete(f'/internal/routes/{route_id}/responses/{response_id}')
        assert response.status_code == 200
        assert response.json()['responses'][0]['body'] == self.payload_route['responses'][1]['body']
        assert response.json()['responses'][0]['status_code'] == self.payload_route['responses'][1]['status_code']

        non_existent_id = uuid.uuid4()
        response = client.delete(f'/internal/routes/{non_existent_id}/responses/{response_id}')

        assert response.status_code == 404
        assert response.json() == {'detail': f'Route "{non_existent_id}" was not found.'}

        response = client.delete(f'/internal/routes/{route_id}/responses/{non_existent_id}')

        assert response.status_code == 404
        assert response.json() == {'detail': f'Response "{non_existent_id}" was not found in route "{route_id}".'}

    def test_delete_route_responses(self, client):
        response = client.post('/internal/routes', json=self.payload_route)
        route_id = response.json()['id']

        response = client.delete(f'internal/routes/{route_id}/responses')

        assert response.status_code == http.HTTPStatus.OK
        assert response.json()['responses'] == []

        non_existent_id = uuid.uuid4()
        response = client.delete(f'/internal/routes/{non_existent_id}/responses')

        assert response.status_code == 404
        assert response.json() == {'detail': f'Route "{non_existent_id}" was not found.'}

    def test_create_route_response(self, client):
        response = client.post('/internal/routes', json=self.payload_route)
        route_id = response.json()['id']

        foo = {'status_code': http.HTTPStatus.OK, 'body': {'some': 'other'}}
        response = client.post(f'/internal/routes/{route_id}/responses', json=foo)

        assert response.status_code == 200
        assert response.json()['responses'][0]['body'] == self.payload_route['responses'][0]['body']
        assert response.json()['responses'][0]['status_code'] == self.payload_route['responses'][0]['status_code']

        non_existent_id = uuid.uuid4()
        response = client.post(f'/internal/routes/{non_existent_id}/responses', json=foo)

        assert response.status_code == 404
        assert response.json() == {'detail': f'Route "{non_existent_id}" was not found.'}

    def test_get_route_response_validators(self, client):
        response = client.post('/internal/routes', json=self.payload_route)
        route_id = response.json()['id']

        response = client.get(f'internal/routes/{route_id}/response_validators')

        assert response.status_code == 200
        assert response.json()[0]['json_schema'] == self.payload_route['response_validators'][0]['json_schema']
        assert response.json()[0]['status_code'] == self.payload_route['response_validators'][0]['status_code']

        non_existent_id = uuid.uuid4()
        response = client.get(f'/internal/routes/{non_existent_id}/response_validators')

        assert response.status_code == 404
        assert response.json() == {'detail': f'Route "{non_existent_id}" was not found.'}

    def test_delete_route_response_validator(self, client):
        response = client.post('/internal/routes', json=self.payload_route)
        route_id = response.json()['id']

        response = client.post(f'/internal/routes/{route_id}/response_validators', json=self.payload_response_validator)
        response_validator_id = response.json()['response_validators'][0]['id']
        remaining_response_validator = response.json()['response_validators'][1]

        response = client.delete(f'/internal/routes/{route_id}/response_validators/{response_validator_id}')

        assert response.status_code == 200
        assert response.json()['response_validators'] == [remaining_response_validator]

        non_existent_id = uuid.uuid4()
        response = client.delete(f'/internal/routes/{route_id}/response_validators/{non_existent_id}')

        assert response.status_code == 404
        assert response.json() == {'detail': f'Response_validator "{non_existent_id}" was not found in route "{route_id}".'}

        response = client.delete(f'/internal/routes/{non_existent_id}/response_validators/{response_validator_id}')

        assert response.status_code == 404
        assert response.json() == {'detail': f'Route "{non_existent_id}" was not found.'}

    def test_delete_route_response_validators(self, client):
        response = client.post('/internal/routes', json=self.payload_route)
        route_id = response.json()['id']

        response = client.delete(f'/internal/routes/{route_id}/response_validators')

        assert response.status_code == 200
        assert response.json()['response_validators'] == []

        non_existent_id = uuid.uuid4()
        response = client.delete(f'/internal/routes/{non_existent_id}/response_validators')

        assert response.status_code == 404
        assert response.json() == {'detail': f'Route "{non_existent_id}" was not found.'}

    def test_create_route_response_validator(self, client):
        response = client.post('/internal/routes', json=self.payload_route)
        route_id = response.json()['id']

        response = client.post(f'/internal/routes/{route_id}/response_validators', json=self.payload_response_validator)
        response_body = response.json()

        assert response.status_code == 200
        assert response_body['response_validators'][1]['json_schema'] == self.payload_response_validator['json_schema']
        assert response_body['response_validators'][1]['status_code'] == self.payload_response_validator['status_code']

        non_existent_id = uuid.uuid4()
        response = client.post(f'/internal/routes/{non_existent_id}/response_validators', json=self.payload_response_validator)

        assert response.status_code == 404
        assert response.json() == {'detail': f'Route "{non_existent_id}" was not found.'}

    def test_get_error_responses(self, client, mocked_config):
        expected_error_responses = [(i.status_code, i.body) for i in mocked_config.settings.error_responses] +\
                                   [(self.payload_error_response['status_code'], self.payload_error_response['body'])]
        client.post(f'/internal/settings/error_responses', json=self.payload_error_response)

        response = client.get('/internal/settings/error_responses')

        assert response.status_code == 200
        assert [(i['status_code'], i['body']) for i in response.json()] == expected_error_responses

    def test_create_error_response(self, client):
        response = client.post(f'/internal/settings/error_responses', json=self.payload_error_response)

        assert response.status_code == 200
        error_response_id = response.json()['id']

        response = client.get(f'/internal/settings/error_responses')

        assert error_response_id in [i['id'] for i in response.json()]
        assert response.json()[1]['status_code'] == self.payload_error_response['status_code']
        assert response.json()[1]['body'] == self.payload_error_response['body']

    def test_delete_error_responses(self, client):
        client.post(f'/internal/settings/error_responses', json=self.payload_error_response)
        response = client.get(f'/internal/settings/error_response')

        assert len(response.json()) != 0

        response = client.delete(f'/internal/settings/error_responses')
        assert response.status_code == 200

        # assert client.get(f'/internal/settings/error_responses').json() == []

    def test_delete_error_response(self, client):
        response = client.post(f'/internal/settings/error_responses', json=self.payload_error_response)
        error_response_id = response.json()['id']

        response = client.delete(f'/internal/settings/error_responses/{error_response_id}')

        assert response.status_code == 200
        assert error_response_id not in [i['id'] for i in response.json()]

        non_existent_id = uuid.uuid4()
        response = client.delete(f'/internal/settings/error_responses/{non_existent_id}')

        assert response.status_code == 404
        assert response.json() == {'detail': f'Error response "{non_existent_id}" was not found.'}
