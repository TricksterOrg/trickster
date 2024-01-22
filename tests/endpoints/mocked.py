from tests.conftest import AUTH_TOKEN


class TestMockedEndpoints:
    def test_mocked_response(self, mocked_router, client):
        result = client.get('/users', headers={'Authorization': f'Bearer {AUTH_TOKEN}'})

        assert result.status_code == 200
        assert result.json() == mocked_router.routes[0].responses[0].body

    def test_mocked_response_non_existent(self, mocked_router, client):
        result = client.get('/non-existent-path', headers={'Authorization': f'Bearer {AUTH_TOKEN}'})
        assert result.status_code == 404

        mocked_router.error_responses = []

        result = client.patch('/users', headers={'Authorization': f'Bearer {AUTH_TOKEN}'})

        assert result.status_code == 404
        assert result.json() == {
            'error': 'Resource error', 'reason': 'No route or response was found for your request.'
        }

    def test_mocked_response_non_authorised(self, mocked_router, client):
        result = client.get('/users')

        assert result.status_code == 401
        assert result.json() == {'auth': 'unauthorized'}
