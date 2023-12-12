class TestHealthcheck:
    def test_healthcheck(self, client):
        response = client.get('/internal/healthcheck')
        assert response.status_code == 200
        assert response.json() == {'status': 'OK'}

    def test_get_routes(self, client):
        response = client.get('/internal/routes')

        assert response.status_code == 200
        assert response.json() == ''

    def test_get_route(self, client):
        ...

    def test_create_route(self, client):
        ...

    def test_delete_routes(self, client):
        ...

    def test_delete_route(self, client):
        ...

    def test_get_route_responses(self, client):
        ...

    def test_delete_route_response(self, client):
        ...

    def test_delete_route_responses(self, client):
        ...

    def test_create_route_response(self, client):
        ...

    def test_get_route_response_validators(self, client):
        ...

    def test_delete_route_response_validator(self, client):
        ...

    def test_delete_route_response_validators(self, client):
        ...

    def test_create_route_response_validator(self, client):
        ...
