import pytest

from werkzeug.exceptions import BadRequest

from trickster.api_app import http_error_handler, ApiApp


@pytest.mark.unit
class TestHttpErrorHandler:
    def test_converts_error_to_json_response(self, app):
        with app.app_context():
            exception = BadRequest('Received invalid request.')
            response, code = http_error_handler(exception)
            print(dir(response))

            assert code == 400
            assert response.get_json() == {
                'error': 'Bad Request',
                'message': 'Received invalid request.'
            }