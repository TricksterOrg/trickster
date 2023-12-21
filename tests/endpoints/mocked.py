import http


class TestMockedEndpoints:
    def test_mocked_response(self, client):
        data = {
            'path': '/testik',
            'responses': [
                {'status_code': http.HTTPStatus.OK, 'body': {'some': 'body'}}
            ],
            'http_method': http.HTTPMethod.POST,
            'response_validators': [
                {
                    'status_code': http.HTTPStatus.OK,
                    'json_schema': {
                        '$schema': 'https://json-schema.org/draft/2020-12/schema',
                        'properties': {'body': {'type': 'string'}}
                    }
                }
            ]
        }
        client.post('/internal/routes', json=data)

        response = client.get('/testik')
        assert response.status_code == 200
        assert response.json() == data['responses'][0]['body']

        response = client.get('/neco')
        assert response.status_code == 404
