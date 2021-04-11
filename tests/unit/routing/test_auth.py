import time
import hashlib

import pytest
import hmac
from werkzeug.exceptions import BadRequest

from trickster.routing import AuthenticationError, RouteConfigurationError
from trickster.routing.auth import NoAuth, TokenAuth, BasicAuth, FormAuth, CookieAuth, HmacAuth, Auth
from trickster.routing.input import IncomingTestRequest


@pytest.mark.unit
class TestAuth:
    def test_deserialize_missing_method(self):
        with pytest.raises(RouteConfigurationError):
            Auth.deserialize({})

    def test_deserialize_unknown_type(self):
        with pytest.raises(RouteConfigurationError):
            Auth.deserialize({'method': 'unknown'})


@pytest.mark.unit
class TestNoAuth:
    def test_serialize(self):
        auth = NoAuth()
        auth.serialize() == None

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
        auth = TokenAuth('abcdefghi')
        auth.serialize() == {
            'method': 'token',
            'token': 'abcdefghi'
        }

    def test_deserialize(self):
        auth = Auth.deserialize({
            'method': 'token',
            'token': 'abcdefghi'
        })
        assert isinstance(auth, TokenAuth)
        assert auth.token == 'abcdefghi'

    def test_authenticate(self):
        auth = TokenAuth('abcdefghi')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            headers={'Authorization': 'Bearer abcdefghi'}
        )
        auth.authenticate(request)

    def test_missing_auth_header(self):
        auth = TokenAuth('abcdefghi')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET'
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_missing_invalid_auth_header(self):
        auth = TokenAuth('abcdefghi')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            headers={'Authorization': 'invalid'}
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_missing_bearer_token(self):
        auth = TokenAuth('abcdefghi')
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
        auth = BasicAuth('username', 'password')
        auth.serialize() == {
            'method': 'basic',
            'username': 'username',
            'password': 'password'
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
        auth = BasicAuth('username', 'password')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            headers={'Authorization': 'dXNlcm5hbWU6cGFzc3dvcmQ='}
        )
        auth.authenticate(request)

    def test_invalid_username_and_password(self):
        auth = BasicAuth('username', 'password')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            headers={'Authorization': 'aW52YWxpZDppbnZhbGlk'}
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_missing_auth_header(self):
        auth = BasicAuth('username', 'password')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET'
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_invalid_auth_token(self):
        auth = BasicAuth('username', 'password')
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
        auth = FormAuth({
            'field1': 'value1',
            'field2': 'value2'
        })
        auth.serialize() == {
            'method': 'basic',
            'fields': {
               'field1': 'value1',
                'field2': 'value2'
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
        auth = FormAuth({
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
        auth = FormAuth({
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
        auth = FormAuth({
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
        auth = CookieAuth('name', 'value')
        auth.serialize() == {
            'method': 'cookie',
            'name': 'name',
            'value': 'value'
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
        auth = CookieAuth('name', 'value')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET',
            cookies={'name': 'value'}
        )
        auth.authenticate(request)

    def test_missing_cookie(self):
        auth = CookieAuth('name', 'value')
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path='/test',
            method='GET'
        )
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_invalid_cookie_value(self):
        auth = CookieAuth('name', 'value')
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
        auth = HmacAuth('secret')
        auth.serialize() == {
            'method': 'hmac',
            'key': 'secret'
        }

    def test_deserialize(self):
        auth = Auth.deserialize({
            'method': 'hmac',
            'key': 'secret'
        })
        assert isinstance(auth, HmacAuth)
        assert auth.key == 'secret'

    def test_authenticate(self):
        auth = HmacAuth('secret')
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
        auth = HmacAuth('secret')
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
        auth = HmacAuth('secret')
        ts = time.time()
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path=f'/test?hmac_timestamp={ts}',
            method='GET'
        )

        with pytest.raises(AuthenticationError):
            auth.authenticate(request)

    def test_signature_in_past(self):
        auth = HmacAuth('secret')
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
        auth = HmacAuth('secret')
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
        auth = HmacAuth('secret')
        ts = time.time()
        request = IncomingTestRequest(
            base_url='http://localhost/',
            full_path=f'/test?hmac_timestamp={ts}&hmac_sign=invalid',
            method='GET'
        )

        with pytest.raises(AuthenticationError):
            auth.authenticate(request)