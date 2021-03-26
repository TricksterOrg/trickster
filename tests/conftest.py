import pytest

from trickster.api_app import ApiApp
from trickster.config import Config


@pytest.fixture
def config():
    return Config()


@pytest.fixture
def app(config):
    return ApiApp(config)


@pytest.fixture
def client(app):
    return app.test_client()
