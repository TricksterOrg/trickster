import pytest

import flask

from trickster.input import IncomingTestRequest, IncomingFlaskRequest, HTTP_METHODS


@pytest.mark.unit
class TestIncomingTestRequest:
    def test_path_strips_query(self):
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/path/file.json?arg1=1&arg2=2#anchor',
            method='GET'
        )
        assert request.path == '/path/file.json'

    def test_parse_query_to_args(self):
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/path/file.json?arg1=1&arg2=2#anchor',
            method='GET'
        )
        assert request.args == {
            'arg1': '1',
            'arg2': '2'
        }

    def test_get_query_string_strips_path(self):
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/path/file.json?arg1=1&arg2=2#anchor',
            method='GET'
        )
        assert request.query_string == 'arg1=1&arg2=2'

    def test_headers_are_always_empty_dict(self):
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/path/file.json?arg1=1&arg2=2#anchor',
            method='GET',
            headers={'header': 'value'}
        )
        assert request.headers == {'header': 'value'}

    def test_form_from_arg(self):
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/path/file.json?arg1=1&arg2=2#anchor',
            method='GET',
            form={'field': 'value'}
        )
        assert request.form == {'field': 'value'}

    def test_cookies_are_alway_empty_dict(self):
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/path/file.json?arg1=1&arg2=2#anchor',
            method='GET',
            cookies={'cookie': 'value'}
        )
        assert request.cookies == {'cookie': 'value'}

    @pytest.mark.parametrize('method', HTTP_METHODS)
    def test_get_method(self, method):
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/path/file.json?arg1=1&arg2=2#anchor',
            method=method
        )
        assert request.method == method


@pytest.mark.unit
class TestIncomingFlaskRequest:
    def test_get_path_from_original_request(self, app):
        with app.test_request_context(
            base_url='http://localhost/',
            path='/path/file.json',
            query_string='?arg1=1&arg2=2',
            method='GET',
            headers={'header': 'value'}
        ):
            request = IncomingFlaskRequest(flask.request)
            assert request.path == '/path/file.json'

    def test_parse_query_to_args(self, app):
        with app.test_request_context(
            base_url='http://localhost/',
            path='/path/file.json',
            query_string='arg1=1&arg2=2',
            method='GET',
            headers={'header': 'value'}
        ):
            request = IncomingFlaskRequest(flask.request)
            assert request.args['arg1'] == '1'
            assert request.args['arg2'] == '2'

    def test_query_string_from_original_request(self, app):
         with app.test_request_context(
            base_url='http://localhost/',
            path='/path/file.json',
            query_string='arg1=1&arg2=2',
            method='GET',
            headers={'header': 'value'}
        ):
            request = IncomingFlaskRequest(flask.request)
            assert request.query_string == 'arg1=1&arg2=2'

    @pytest.mark.parametrize('method', HTTP_METHODS)
    def test_get_method_from_original_request(self, app, method):
        with app.test_request_context(
            base_url='http://localhost/',
            path='/path/file.json',
            query_string='arg1=1&arg2=2',
            method=method,
            headers={'header': 'value'}
        ):
            request = IncomingFlaskRequest(flask.request)
            assert request.method == method

    def test_headers_are_parsed_to_dict(self, app):
        with app.test_request_context(
            base_url='http://localhost/',
            path='/path/file.json',
            query_string='arg1=1&arg2=2',
            method='GET',
            headers={'header': 'value'}
        ):
            request = IncomingFlaskRequest(flask.request)
            assert request.headers['Header'] == 'value'

    def test_get_url_combines_all_parts(self, app):
        with app.test_request_context(
            base_url='http://localhost/',
            path='/path/file.json',
            query_string='arg1=1&arg2=2',
            method='GET',
            headers={'header': 'value'}
        ):
            request = IncomingFlaskRequest(flask.request)
            assert request.url == 'http://localhost/path/file.json?arg1=1&arg2=2'

    def test_cookies_are_parsed_to_dict(self, app):
        with app.test_request_context(
            base_url='http://localhost/',
            path='/path/file.json',
            query_string='arg1=1&arg2=2',
            method='GET',
            headers={'header': 'value'}
        ):
            request = IncomingFlaskRequest(flask.request)
            assert len(request.cookies) == 0

    def test_form_is_parsed_to_dict(self, app):
        with app.test_request_context(
            base_url='http://localhost/',
            path='/path/file.json',
            query_string='arg1=1&arg2=2',
            method='GET',
            headers={'header': 'value'},
        ):
            request = IncomingFlaskRequest(flask.request)
            assert len(request.form) == 0