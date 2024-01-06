import os
import pathlib
import http

import pytest

from fastapi.testclient import TestClient

from trickster.trickster_app import create_app
from trickster.config import get_config
from trickster.meta import project_root
from trickster.router import get_router
from trickster.model import Route

mocked_files_path = project_root / 'tests/mocked_files'


@pytest.fixture(scope='function', autouse=True)
def mocked_config(mocker, request):
    file_path_arg = getattr(request, 'param', mocked_files_path / 'config.json')
    get_config.cache_clear()
    mocker.patch.dict(os.environ, {'TRICKSTER_CONF_PATH': str(file_path_arg)})
    yield get_config()
    get_config.cache_clear()


@pytest.fixture(scope='function')
def mocked_router():
    payload_route = {
        'path': '/users',
        'response_selector': 'first',
        'responses': [
            {
                'status_code': http.HTTPStatus.OK, 'body': {'user_id': 1234, 'user_name': 'Mark Twain'}
            },
            {
                'status_code': http.HTTPStatus.OK, 'body': {'user_id': 5678, 'user_name': 'Charles Dickens'}
            }
        ],
        'http_methods': [http.HTTPMethod.GET],
        'response_validators': [
            {
                'status_code': http.HTTPStatus.OK,
                'json_schema': {
                    '$schema': 'https://json-schema.org/draft/2020-12/schema',
                    'required': ['user_id'],
                    'properties': {'user_id': {'type': 'number'}, 'user_name': {'type': 'string'}}
                }
            }
        ]
    }

    router = get_router(config=get_config())
    router.add_route(Route(**payload_route))

    yield router

    get_router.cache_clear()


@pytest.fixture(scope='function')
def mocked_router_empty():
    get_router.cache_clear()
    router = get_router(config=get_config())

    yield router

    get_router.cache_clear()


@pytest.fixture(scope='session')
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(scope='function')
def mocked_openapi(mocked_config, request):
    file_path_arg = getattr(request, 'param', mocked_files_path / 'openapi.yaml')

    get_router.cache_clear()
    orig_config = mocked_config.openapi_boostrap
    mocked_config.openapi_boostrap = pathlib.Path(file_path_arg)
    yield
    get_router.cache_clear()
    mocked_config.openapi_boostrap = orig_config
