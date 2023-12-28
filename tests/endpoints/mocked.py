import http


class TestMockedEndpoints:
    def test_mocked_response(self, client):
        payload_route = {
            'path': '/users',
            'response_selector': 'first',
            'responses': [
                {
                    'status_code': http.HTTPStatus.OK, 'body': {'user_id': 1234, 'user_name': 'Mark Twain'}
                },
                {
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
        client.post('/internal/routes', json=payload_route)

        response = client.get('/users')
        assert response.status_code == 200
        assert response.json() == payload_route['responses'][0]['body']

        response = client.get('/non-existent-path')
        assert response.status_code == 404
