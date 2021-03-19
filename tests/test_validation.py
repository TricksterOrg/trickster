import pytest
from pathlib import Path

import flask
from fastjsonschema.exceptions import JsonSchemaValueException

from trickster.validation import request_schema, compile_json_schema, get_schema_path


@pytest.mark.unit
class TestJsonSchemaValidation:
    def test_schema_path(self):
        path = get_schema_path('route.schema.json')
        assert path.name == 'route.schema.json'
        assert path.is_absolute
        assert path.exists()

    def test_compile_json_schema_is_cached(self):
        validator1 = compile_json_schema(get_schema_path('route.schema.json'))
        validator2 = compile_json_schema(get_schema_path('route.schema.json'))
        assert validator1 is validator2

    def test_compile_json_schema_valid(self, tmpdir):
        schema = tmpdir.join('test.schema.json')
        schema.write('''{
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"property": {"type": "number"}},
            "required": ["property"]
        }''')
        validator = compile_json_schema(Path(schema))
        validator({'property': 2})

    def test_compile_json_schema_invalid(self, tmpdir):
        schema = tmpdir.join('test.schema.json')
        schema.write('''{
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"property": {"type": "number"}},
            "required": ["property"]
        }''')
        validator = compile_json_schema(Path(schema))
        with pytest.raises(JsonSchemaValueException):
            validator({'property': 'string'})

    def test_schema_decorator_valid(self):
        app = flask.Flask(__name__)

        @app.route('/', methods=['POST'])
        @request_schema('request.schema.json')
        def endpoint():
            return 'success'

        with app.test_client() as client:
            response = client.post('/', json={
                'path': '/',
                'method': 'GET'
            })
            assert response.data == b'success'
            assert response.status_code == 200

    def test_schema_decorator_invalid(self):
        app = flask.Flask(__name__)

        @app.route('/', methods=['POST'])
        @request_schema('request.schema.json')
        def endpoint():
            return 'success'

        with app.test_client() as client:
            response = client.post('/', json={
                'invalid': True
            })
            assert response.status_code == 400