import pytest
from fastapi import FastAPI

from trickster.trickster_app import create_app, load_openapi_routes
from trickster.router import get_router


class TestCreateApp:
    def test_create_app(self):
        assert isinstance(create_app(), FastAPI)


class TestLoadOpenapiRoutes:

    def test_load_openapi(self, mocked_openapi):
        load_openapi_routes()
        assert len(get_router().routes) == 2

    @pytest.mark.parametrize('mocked_openapi', ['nonexistent.yaml'], indirect=True)
    def test_non_existent_openapi(self, mocked_openapi):
        load_openapi_routes()
        assert get_router().routes == []
