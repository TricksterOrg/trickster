"""Integration tests of external API endpoints."""

import pytest


@pytest.mark.integration
class TestExternalEndpoints:
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
