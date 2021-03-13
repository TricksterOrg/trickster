import flask
import pytest
from fastjsonschema import JsonSchemaException

from trickster.validation import compile_json_schema, get_schema_path, request_schema


@pytest.mark.unit
class TestValidation:
    def test_get_schema_path(self):
        path = get_schema_path('some.schema.json')
        assert path.match('*/mock/schemas/some.schema.json')
