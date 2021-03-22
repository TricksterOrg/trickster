import pytest

import flask

from trickster.input import IncomingTestRequest, IncomingFlaskRequest, HTTP_METHODS


@pytest.mark.unit
class TestIncomingTestRequest:
    def test_path(self):
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/path/file.json?arg1=1&arg2=2#anchor',
            method='GET'
        )
        assert request.path == '/path/file.json'

    def test_args(self):
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/path/file.json?arg1=1&arg2=2#anchor',
            method='GET'
        )
        assert request.args == {
            'arg1': '1',
            'arg2': '2'
        }

    def test_query_string(self):
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/path/file.json?arg1=1&arg2=2#anchor',
            method='GET'
        )
        assert request.query_string == 'arg1=1&arg2=2'

    def test_headers(self):
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/path/file.json?arg1=1&arg2=2#anchor',
            method='GET'
        )
        assert request.headers == {}

    def test_form(self):
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/path/file.json?arg1=1&arg2=2#anchor',
            method='GET'
        )
        assert request.form == {}

    def test_cookies(self):
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/path/file.json?arg1=1&arg2=2#anchor',
            method='GET'
        )
        assert request.cookies == {}

    @pytest.mark.parametrize('method', HTTP_METHODS)
    def test_method(self, method):
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/path/file.json?arg1=1&arg2=2#anchor',
            method=method
        )
        assert request.method == method


@pytest.mark.unit
class TestIncomingFlaskRequest:

    def test_path(self, app):
        with app.test_request_context(
            base_url='http://localhost/',
            path='/path/file.json',
            query_string='?arg1=1&arg2=2',
            method='GET',
            headers={'header': 'value'}
        ):
            request = IncomingFlaskRequest(flask.request)
            assert request.path == '/path/file.json'

    def test_args(self, app):
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

    def test_query_string(self, app):
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
    def test_method(self, app, method):
        with app.test_request_context(
            base_url='http://localhost/',
            path='/path/file.json',
            query_string='arg1=1&arg2=2',
            method=method,
            headers={'header': 'value'}
        ):
            request = IncomingFlaskRequest(flask.request)
            assert request.method == method

    def test_headers(self, app):
        with app.test_request_context(
            base_url='http://localhost/',
            path='/path/file.json',
            query_string='arg1=1&arg2=2',
            method='GET',
            headers={'header': 'value'}
        ):
            request = IncomingFlaskRequest(flask.request)
            assert request.headers['Header'] == 'value'

    def test_url(self, app):
        with app.test_request_context(
            base_url='http://localhost/',
            path='/path/file.json',
            query_string='arg1=1&arg2=2',
            method='GET',
            headers={'header': 'value'}
        ):
            request = IncomingFlaskRequest(flask.request)
            assert request.url == 'http://localhost/path/file.json?arg1=1&arg2=2'

    def test_cookies(self, app):
        with app.test_request_context(
            base_url='http://localhost/',
            path='/path/file.json',
            query_string='arg1=1&arg2=2',
            method='GET',
            headers={'header': 'value'}
        ):
            request = IncomingFlaskRequest(flask.request)
            assert len(request.cookies) == 0

    def test_form(self, app):
        with app.test_request_context(
            base_url='http://localhost/',
            path='/path/file.json',
            query_string='arg1=1&arg2=2',
            method='GET',
            headers={'header': 'value'},
        ):
            request = IncomingFlaskRequest(flask.request)
            assert len(request.form) == 0