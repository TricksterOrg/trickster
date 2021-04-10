import pytest
from pathlib import Path


@pytest.mark.integration
class TestUtilityEndpoints:
    def test_get_health(self, client):
        response = client.get('/internal/health')

        assert response.status_code == 200
        assert response.json == {'status': 'ok'}

    def test_reset(self, client):
        client.post('/internal/routes', json={
            'path': '/path',
            'responses': [
                {
                   'body': 'response_body'
                }
            ]
        })
        response = client.post('/internal/reset')
        assert response.status_code == 204

        response = client.get('/internal/routes')
        assert response.status_code == 200
        assert response.json == []
