"""This module provides validation of incomming requests."""

import json
import flask
import functools
import fastjsonschema
import pathlib

from typing import Callable, Any, Dict, List


schemas_path = pathlib.Path(__file__).parent / 'schemas'


def request_schema(schema_name: str) -> Callable:
    """Validate current request payload with given json schema.

    `request_schema` can be used only as a flask endpoint decorator. Must be
    called within request scope.
    """
    def request_schema_decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def request_schema_wrapper(*args: List[Any], **kwargs: Dict[str, Any]) -> Any:
            try:
                payload = flask.request.get_json()
                schema_path = get_schema_path(schema_name)
                validator = compile_json_schema(schema_path)
                validator(payload)
                return func(*args, **kwargs)
            except fastjsonschema.JsonSchemaException as e:
                flask.abort(400, e.message)
        return request_schema_wrapper
    return request_schema_decorator


@functools.lru_cache
def compile_json_schema(schema_path: pathlib.Path) -> Callable:
    """Compiles given schema to fastjson validation function."""
    with open(schema_path.absolute()) as schema_file:
        schema = json.load(schema_file)
        return fastjsonschema.compile(schema)


def get_schema_path(schema_name: str) -> pathlib.Path:
    """Return path to json schema file."""
    return schemas_path / schema_name
