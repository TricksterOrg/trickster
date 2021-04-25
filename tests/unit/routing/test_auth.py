import time
import hashlib

import pytest
import hmac
from werkzeug.exceptions import BadRequest

from trickster.routing import AuthenticationError, Delay, Response, RouteConfigurationError, ResponseBody
from trickster.routing.auth import NoAuth, TokenAuth, BasicAuth, FormAuth, CookieAuth, HmacAuth, Auth, AuthWithResponse
from trickster.routing.input import IncomingTestRequest


@pytest.mark.unit
class TestAuth:
    def test_deserialize_missing_method(self):
        with pytest.raises(RouteConfigurationError):
            Auth.deserialize({})

    def test_deserialize_unknown_type(self):
        with pytest.raises(RouteConfigurationError):
            Auth.deserialize({'method': 'unknown'})

    def test_deserialize(self):
        auth = Auth.deserialize({'method': None})
        assert isinstance(auth, NoAuth)


@pytest.mark.unit
class TestAuthWithResponse:
    def test_deserialize_missing_method(self):
        with pytest.raises(RouteConfigurationError):
            AuthWithResponse.deserialize({})

    def test_deserialize_unknown_type(self):
        with pytest.raises(RouteConfigurationError):
            AuthWithResponse.deserialize({'method': 'unknown'})

    def test_deserialize_with_string_response(self):
        auth = AuthWithResponse.deserialize({
            'method': 'token',
            'token': 'abcdefghi',
            'unauthorized_response': {
                'body': 'unauthorized'
            }
        })
        assert isinstance(auth, TokenAuth)
        assert auth.token == 'abcdefghi'
        assert isinstance(auth.unauthorized_response.body, ResponseBody)
        assert auth.unauthorized_response.body.content == 'unauthorized'


@pytest.mark.unit
class TestNoAuth:
    def test_serialize(self):
        auth = NoAuth()
        assert auth.serialize() == None

    def test_deserialize(self):
        auth = Auth.deserialize(None)
        assert isinstance(auth, NoAuth)

    def test_always_authenticates(self):
        auth = NoAuth()
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET'
        )
        auth.authenticate(request)


@pytest.mark.unit
class TestTokenAuth:
    def test_serialize(self):
        auth = TokenAuth(Response(ResponseBody('test'), Delay()), 'abcdefghi')
        assert auth.serialize() == {
            'method': 'token',
            'token': 'abcdefghi',
            'unauthorized_response': {
                'body': 'test',
                'delay': 0.0,
                'headers': {},
                'status': 200,
                'used_count': 0
            }
        }

    def test_deserialize(self):
        auth = Auth.deserialize({
            'method': 'token',
            'token': 'abcdefghi'
        })
        assert isinstance(auth, TokenAuth)
        assert auth.token == 'abcdefghi'

    def test_authenticate(self):
        auth = TokenAuth(Response(ResponseBody(''), Delay()), 'abcdefghi')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            headers={'Authorization': 'Bearer abcdefghi'}
        )
        auth.authenticate(request)

    def test_missing_auth_header(self):
        auth = TokenAuth(Response(ResponseBody(''), Delay()), 'abcdefghi')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET'
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_missing_invalid_auth_header(self):
        auth = TokenAuth(Response(ResponseBody(''), Delay()), 'abcdefghi')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            headers={'Authorization': 'invalid'}
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_missing_bearer_token(self):
        auth = TokenAuth(Response(ResponseBody(''), Delay()), 'abcdefghi')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            headers={'Authorization': 'Bearer xxxxxxx'}
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)


@pytest.mark.unit
class TestBasicAuth:
    def test_serialize(self):
        auth = BasicAuth(Response(ResponseBody('test'), Delay()), 'username', 'password')
        assert auth.serialize() == {
            'method': 'basic',
            'username': 'username',
            'password': 'password',
            'unauthorized_response': {
                'body': 'test',
                'delay': 0.0,
                'headers': {},
                'status': 200,
                'used_count': 0
            }
        }

    def test_deserialize(self):
        auth = Auth.deserialize({
            'method': 'basic',
            'username': 'username',
            'password': 'password'
        })
        assert isinstance(auth, BasicAuth)
        assert auth.username == 'username'
        assert auth.password == 'password'

    def test_authenticate(self):
        auth = BasicAuth(Response(ResponseBody(''), Delay()), 'username', 'password')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            headers={'Authorization': 'dXNlcm5hbWU6cGFzc3dvcmQ='}
        )
        auth.authenticate(request)

    def test_invalid_username_and_password(self):
        auth = BasicAuth(Response(ResponseBody(''), Delay()), 'username', 'password')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            headers={'Authorization': 'aW52YWxpZDppbnZhbGlk'}
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_missing_auth_header(self):
        auth = BasicAuth(Response(ResponseBody(''), Delay()), 'username', 'password')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET'
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_invalid_auth_token(self):
        auth = BasicAuth(Response(ResponseBody(''), Delay()), 'username', 'password')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            headers={'Authorization': 'xxx'}
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)


@pytest.mark.unit
class TestFormAuth:
    def test_serialize(self):
        auth = FormAuth(Response(ResponseBody('test'), Delay()), {
            'field1': 'value1',
            'field2': 'value2'
        })
        assert auth.serialize() == {
            'method': 'form',
            'fields': {
               'field1': 'value1',
                'field2': 'value2'
            },
            'unauthorized_response': {
                'body': 'test',
                'delay': 0.0,
                'headers': {},
                'status': 200,
                'used_count': 0
            }
        }

    def test_deserialize(self):
        auth = Auth.deserialize({
            'method': 'form',
            'fields': {
               'field1': 'value1',
                'field2': 'value2'
            }
        })
        assert isinstance(auth, FormAuth)
        assert auth.fields == {
           'field1': 'value1',
            'field2': 'value2'
        }

    def test_authenticate(self):
        auth = FormAuth(Response(ResponseBody(''), Delay()), {
            'field1': 'value1',
            'field2': 'value2'
        })
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            form={
                'field1': 'value1',
                'field2': 'value2'
            }
        )
        auth.authenticate(request)

    def test_missing_field(self):
        auth = FormAuth(Response(ResponseBody(''), Delay()), {
            'field1': 'value1',
            'field2': 'value2'
        })
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            form={
                'field1': 'value1'
            }
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_invalid_field_value(self):
        auth = FormAuth(Response(ResponseBody(''), Delay()), {
            'field1': 'value1',
            'field2': 'value2'
        })
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            form={
                'field1': 'value1',
                'field2': 'invalid'
            }
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)


@pytest.mark.unit
class TestCookieAuth:
    def test_serialize(self):
        auth = CookieAuth(Response(ResponseBody('test'), Delay()), 'name', 'value')
        assert auth.serialize() == {
            'method': 'cookie',
            'name': 'name',
            'value': 'value',
            'unauthorized_response': {
                'body': 'test',
                'delay': 0.0,
                'headers': {},
                'status': 200,
                'used_count': 0
            }
        }

    def test_deserialize(self):
        auth = Auth.deserialize({
            'method': 'cookie',
            'name': 'name',
            'value': 'value'
        })
        assert isinstance(auth, CookieAuth)
        assert auth.name == 'name'
        assert auth.value == 'value'

    def test_authenticate(self):
        auth = CookieAuth(Response(ResponseBody(''), Delay()), 'name', 'value')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            cookies={'name': 'value'}
        )
        auth.authenticate(request)

    def test_missing_cookie(self):
        auth = CookieAuth(Response(ResponseBody(''), Delay()), 'name', 'value')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET'
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_invalid_cookie_value(self):
        auth = CookieAuth(Response(ResponseBody(''), Delay()), 'name', 'value')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            cookies={'name': 'invalid'}
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)


@pytest.mark.unit
class TestHmacAuth:
    def test_serialize(self):
        auth = HmacAuth(Response(ResponseBody('test'), Delay()), 'secret')
        assert auth.serialize() == {
            'method': 'hmac',
            'key': 'secret',
            'unauthorized_response': {
                'body': 'test',
                'delay': 0.0,
                'headers': {},
                'status': 200,
                'used_count': 0
            }
        }

    def test_deserialize(self):
        auth = Auth.deserialize({
            'method': 'hmac',
            'key': 'secret'
        })
        assert isinstance(auth, HmacAuth)
        assert auth.key == 'secret'

    def test_authenticate(self):
        auth = HmacAuth(Response(ResponseBody(''), Delay()), 'secret')
        ts = time.time()
        hash_maker = hmac.new('secret'.encode('utf-8'), digestmod=hashlib.sha1) 
        hash_maker.update(f'/test?hmac_timestamp={ts}'.encode('utf-8'))
        sign = hash_maker.hexdigest() 
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path=f'/test?hmac_timestamp={ts}&hmac_sign={sign}',
            method='GET'
        )
        auth.authenticate(request)

    def test_missing_timestamp(self):
        auth = HmacAuth(Response(ResponseBody(''), Delay()), 'secret')
        ts = time.time()
        hash_maker = hmac.new('secret'.encode('utf-8'), digestmod=hashlib.sha1) 
        hash_maker.update(f'/test'.encode('utf-8'))
        sign = hash_maker.hexdigest() 
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path=f'/test?hmac_sign={sign}',
            method='GET'
        )

        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_missing_sign(self):
        auth = HmacAuth(Response(ResponseBody(''), Delay()), 'secret')
        ts = time.time()
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path=f'/test?hmac_timestamp={ts}',
            method='GET'
        )

        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_signature_in_past(self):
        auth = HmacAuth(Response(ResponseBody(''), Delay()), 'secret')
        ts = 946684861  # 01/01/2020
        hash_maker = hmac.new('secret'.encode('utf-8'), digestmod=hashlib.sha1) 
        hash_maker.update(f'/test?hmac_timestamp={ts}'.encode('utf-8'))
        sign = hash_maker.hexdigest() 
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path=f'/test?hmac_timestamp={ts}&hmac_sign={sign}',
            method='GET'
        )

        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_signature_in_future(self):
        auth = HmacAuth(Response(ResponseBody(''), Delay()), 'secret')
        ts = 13569465661  # 01/01/2400
        hash_maker = hmac.new('secret'.encode('utf-8'), digestmod=hashlib.sha1) 
        hash_maker.update(f'/test?hmac_timestamp={ts}'.encode('utf-8'))
        sign = hash_maker.hexdigest() 
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path=f'/test?hmac_timestamp={ts}&hmac_sign={sign}',
            method='GET'
        )

        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_invalid_sign(self):
        auth = HmacAuth(Response(ResponseBody(''), Delay()), 'secret')
        ts = time.time()
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path=f'/test?hmac_timestamp={ts}&hmac_sign=invalid',
            method='GET'
        )

        with pytest.raises(AuthenticationError):
            auth.authenticate(request)