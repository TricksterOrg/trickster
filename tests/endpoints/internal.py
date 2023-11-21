class TestHealthcheck:
    def test_healthcheck(self, client):
        response = client.get('/internal/healthcheck')
        assert response.status_code == 200
        assert response.json() == {'status': 'OK'}
