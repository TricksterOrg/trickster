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

    def test_coalesce(self):
        config = Config()
        assert config._coalesce(None, None, 1) == 1

    def test_coalesce_all_none(self):
        config = Config()
        assert config._coalesce(None, None, None) is None

    def test_coalesce_no_arguments(self):
        config = Config()
        assert config._coalesce() is None