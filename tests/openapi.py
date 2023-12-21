import pathlib

from openapi_parser import parse

from trickster.openapi import OpenApiSpec
from tests.conftest import mocked_files_path


class TestOpenApiSpec:
    def test_load(self):
        open_api_path = mocked_files_path / 'openapi.yaml'
        parsed_spec = parse(uri=pathlib.Path.as_uri(open_api_path))

        loaded_spec = OpenApiSpec.load(open_api_path)

        assert loaded_spec.spec.paths == parsed_spec.paths
        assert loaded_spec.spec.schemas == parsed_spec.schemas
        assert loaded_spec.spec.info == parsed_spec.info

    def test_get_routes(self):
        open_api_path = mocked_files_path / 'openapi.yaml'
        parsed_spec = parse(uri=pathlib.Path.as_uri(open_api_path))
        expected_paths_in_spec = [path.url for path in parsed_spec.paths]

        loaded_spec = OpenApiSpec.load(open_api_path)
        paths = [route.path.path for route in loaded_spec.get_routes()]

        assert sorted(paths) == sorted(expected_paths_in_spec)
