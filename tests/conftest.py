import pytest

from app import app as api_app


@pytest.fixture
def app():
    return api_app