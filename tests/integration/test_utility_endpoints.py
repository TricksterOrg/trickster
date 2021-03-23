import pytest
from pathlib import Path


@pytest.mark.integration
class TestUtilityEndpoints:
    def test_get_health(self, client):
        response = client.get('/internal/health')

        assert response.status_code == 200
        assert response.json == {'status': 'ok'}
