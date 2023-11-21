"""Functionality to work with OpenApi format."""

import pathlib

from openapi_parser import parse
from openapi_parser import specification as openspec

from trickster.router import Route, ResponseValidator
from trickster.utils import remove_none_values

from typing import Self, Any, cast


class OpenApiSpec:
    """OpenApi specification adapter."""

    JSON_SCHEMA_VERSION = 'https://json-schema.org/draft/2020-12/schema'

    def __init__(self, spec: openspec.Specification) -> None:
        self.spec = spec

    @classmethod
    def load(cls, spec_file: pathlib.Path) -> Self:
        """Load OpenApi spec from a file."""
        if spec_file.exists():
            spec = parse(str(spec_file))
            return cls(spec)
        else:
            # We can't rely on ParserError because openapi_parser raises the same error for any problem with parsing
            raise FileNotFoundError(f'OpenApi specification file "{spec_file}" was not found.')

    def _get_operation_method(self, operation: openspec.Operation) -> str:
        """Get http method from operation."""
        return operation.method.value.upper()

    def _get_path_and_operation_url(self, path: openspec.Path, operation: openspec.Operation) -> str:
        """Get URL path from path and operation."""
        url = path.url
        for parameter in operation.parameters:
            if parameter.location == openspec.ParameterLocation.PATH:
                parameter_type = parameter.schema.type.value
                url = url.replace(f'{parameter.name}', f'{parameter.name}:{parameter_type}')
        return url

    def _schema_to_base_json_schema(self, schema: openspec.Schema) -> dict[str, Any]:
        """Prepare common parameters of json schema from openapi schema."""
        if schema is not None:
            return {
                'title': schema.title,
                'description': schema.description,
                'type': schema.type.value
            }
        return {}

    def _object_schema_to_json_schema(self, schema: openspec.Object) -> dict[str, Any]:
        """Create json schema from object openapi schema."""
        return {
            **self._schema_to_base_json_schema(schema),
            'required': schema.required,
            'properties': {prop.name: self._schema_to_json_schema(prop.schema) for prop in schema.properties},
        }

    def _string_schema_to_json_schema(self, schema: openspec.String) -> dict[str, Any]:
        """Create json schema from string openapi schema."""
        return {
            **self._schema_to_base_json_schema(schema),
            'enum': schema.enum if schema.enum != [] else None,
            'format': schema.format.value if schema.format else None,
            'pattern': schema.pattern
        }

    def _array_schema_to_json_schema(self, schema: openspec.Array) -> dict[str, Any]:
        """Create json schema from array openapi schema."""
        return {
            **self._schema_to_base_json_schema(schema),
            'items': self._schema_to_json_schema(schema.items)
        }

    def _number_schema_to_json_schema(self, schema: openspec.Number) -> dict[str, Any]:
        """Create json schema from integer or float openapi schema."""
        return {
            **self._schema_to_base_json_schema(schema),
            'minimum': schema.minimum,
            'maximum': schema.maximum
        }

    def _anyof_schema_to_json_schema(self, schema: openspec.AnyOf) -> dict[str, Any]:
        """Create json schema from anyOf openapi schema."""
        return {
            'anyOf': [self._schema_to_json_schema(item_schema) for item_schema in schema.schemas]
        }

    def _schema_to_json_schema(self, schema: openspec.Schema, is_root=False) -> dict[str, Any]:
        """Recursively convert openapi schema to json schema."""
        result = {'$schema': self.JSON_SCHEMA_VERSION} if is_root else {}
        if schema is not None:
            match schema.type:
                case openspec.DataType.OBJECT:
                    result.update(self._object_schema_to_json_schema(cast(openspec.Object, schema)))
                case openspec.DataType.STRING:
                    result.update(self._string_schema_to_json_schema(cast(openspec.String, schema)))
                case openspec.DataType.ARRAY:
                    result.update(self._array_schema_to_json_schema(cast(openspec.Array, schema)))
                case openspec.DataType.INTEGER | openspec.DataType.NUMBER:
                    result.update(self._number_schema_to_json_schema(cast(openspec.Number, schema)))
                case openspec.DataType.ANY_OF:
                    result.update(self._anyof_schema_to_json_schema((cast(openspec.AnyOf, schema))))
                case openspec.DataType.NULL | openspec.DataType.BOOLEAN:
                    result.update(self._schema_to_base_json_schema(schema))
                case _:
                    raise ValueError(f'Unsupported schema type {schema.type}')
        return remove_none_values(result)

    def _get_response_validators_from_responses(self, responses: list[openspec.Response]) -> list[ResponseValidator]:
        """Get list of response validators."""
        validators = []
        for response in responses:
            if response.content:
                validator = ResponseValidator(
                    status_code=response.code,  # type: ignore
                    json_schema=self._schema_to_json_schema(response.content[0].schema, is_root=True)
                )
                validators.append(validator)
        return validators

    def get_routes(self) -> list[Route]:
        """Get Trickster routes from OpenApi specification."""
        routes = []
        for path in self.spec.paths:
            for operation in path.operations:
                route = Route(
                    path=self._get_path_and_operation_url(path, operation),  # type: ignore
                    http_methods=[self._get_operation_method(operation)],  # type: ignore
                    response_validators=self._get_response_validators_from_responses(operation.responses)
                )
                routes.append(route)
        return routes
