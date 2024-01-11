class TestMockedEndpoints:
    def test_mocked_response(self, mocked_router, client):
        result = client.get('/users')

        assert result.status_code == 200
        assert result.json() == mocked_router.routes[0].responses[0].body

    def test_mocked_response_non_existent(self, mocked_router, client):
        result = client.get('/non-existent-path')
        assert result.status_code == 404

        mocked_router.error_responses = []

        result = client.patch('/users')

        assert result.status_code == 404
        assert result.json() == {'detail': 'No route or response was found for your request.'}
