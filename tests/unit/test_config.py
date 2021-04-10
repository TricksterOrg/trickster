from pathlib import Path
import json

import pytest

from trickster.config import Config


@pytest.mark.unit
class TestConfig:
    def test_default_port(self):
        config = Config()
        assert config.PORT == Config.DEFAULT_PORT

    def test_user_defined_port(self):
        config = Config(port=12345)
        assert config.PORT == 12345

    def test_port_from_env(self, monkeypatch):
        monkeypatch.setenv('TRICKSTER_PORT', '54321')
        config = Config()
        assert config.PORT == 54321

    def test_user_defined_port_takes_precedence(self, monkeypatch):
        monkeypatch.setenv('TRICKSTER_PORT', '54321')
        config = Config(port=12345)
        assert config.PORT == 12345

    def test_default_url_prefix(self):
        config = Config()
        assert config.INTERNAL_PREFIX == Config.DEFAULT_INTERNAL_PREFIX

    def test_user_defined_url_prefix(self):
        config = Config(internal_prefix='/api')
        assert config.INTERNAL_PREFIX == '/api'

    def test_url_prefix_from_env(self, monkeypatch):
        monkeypatch.setenv('TRICKSTER_INTERNAL_PREFIX', '/test')
        config = Config()
        assert config.INTERNAL_PREFIX == '/test'

    def test_user_defined_url_prefix_takes_precedence(self, monkeypatch):
        monkeypatch.setenv('TRICKSTER_INTERNAL_PREFIX', '/test')
        config = Config(internal_prefix='/api')
        assert config.INTERNAL_PREFIX == '/api'

    def test_routes_path_from_env(self, monkeypatch):
        monkeypatch.setenv('TRICKSTER_ROUTES', '/test.json')
        config = Config()
        assert config.ROUTES_PATH == Path('/test.json')

    def test_default_routes_path(self):
        config = Config()
        assert config.ROUTES_PATH is None

    def test_user_defined_routes_path(self):
        config = Config(routes_path='/path.json')
        assert config.ROUTES_PATH == Path('/path.json')

    def test_user_defined_routes_path_takes_precedence(self, monkeypatch):
        monkeypatch.setenv('TRICKSTER_ROUTES', '/test1.json')
        config = Config(routes_path='/test2.json')
        assert config.ROUTES_PATH == Path('/test2.json')

    def test_default_routes_empty(self):
        config = Config()
        assert config.DEFAULT_ROUTES == []

    def test_default_routes(self, tmpdir):
        routes = [
            {
                "path": "/route1",
                "responses": [
                    {
                        "body": "response1"
                    }
                ]
            },
            {
                "path": "/route2",
                "responses": [
                    {
                        "body": "response2"
                    }
                ]
            }
        ]
        routes_file = tmpdir.join('test.json')
        routes_file.write(json.dumps(routes))
        config = Config(routes_path=routes_file)
        assert config.DEFAULT_ROUTES == routes

    def test_coalesce(self):
        config = Config()
        assert config._coalesce(None, None, 1) == 1

    def test_coalesce_all_none(self):
        config = Config()
        assert config._coalesce(None, None, None) is None

    def test_coalesce_no_arguments(self):
        config = Config()
        assert config._coalesce() is None
