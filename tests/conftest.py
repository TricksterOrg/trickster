import pytest

from trickster.api_app import ApiApp


@pytest.fixture
def app():
    return ApiApp()


@pytest.fixture
def client(app):
    return app.test_client()
