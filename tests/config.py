import os
import json

import pytest
import pydantic

from trickster.config import Config, JsonConfigSettingsSource, ConfigError, get_config


config_data = {
    'internal_prefix': '/int'
}


class TestJsonConfigSettingsSource:
    def test_load_existing_config(self, tmpdir, mocker):
        config_file = tmpdir.join('config.json')
        config_file.write(json.dumps(config_data))
        mocker.patch.dict(os.environ, {'TRICKSTER_CONF_PATH': str(config_file)})

        config_source = JsonConfigSettingsSource(Config)
        assert config_source() == config_data

    def test_load_empty_config(self, tmpdir, mocker):
        config_file = tmpdir.join('config.json')
        mocker.patch.dict(os.environ, {'TRICKSTER_CONF_PATH': str(config_file)})

        with pytest.raises(ConfigError):
            JsonConfigSettingsSource(Config)

    def test_load_default_config(self, tmpdir, mocker):
        config_file = tmpdir.join('config.json')
        config_file.write(json.dumps(config_data))
        mocker.patch(
            'trickster.config.JsonConfigSettingsSource.default_config_file_path',
            new_callable=mocker.PropertyMock,
            return_value=str(config_file)
        )

        config_source = JsonConfigSettingsSource(Config)
        assert config_source() == config_data

    def test_get_field_value(self, tmpdir, mocker):
        config_file = tmpdir.join('config.json')
        config_file.write(json.dumps(config_data))
        mocker.patch.dict(os.environ, {'TRICKSTER_CONF_PATH': str(config_file)})

        config_source = JsonConfigSettingsSource(Config)
        assert config_source.get_field_value(
            pydantic.fields.FieldInfo(), 'internal_prefix'
        ) == ('/int', 'internal_prefix', False)


class TestConfig:
    def test_defaults(self, tmpdir, mocker):
        config_file = tmpdir.join('config.json')
        config_file.write(json.dumps({}))
        mocker.patch.dict(os.environ, {'TRICKSTER_CONF_PATH': str(config_file)})

        config = Config()
        assert config.model_dump() == {
            'internal_prefix': '/internal',
            'openapi_boostrap': None,
            'logging': {'version': 1}
        }


class TestGetConfig:
    def test_caches_config(self, tmpdir, mocker):
        config_file = tmpdir.join('config.json')
        config_file.write(json.dumps({}))
        mocker.patch.dict(os.environ, {'TRICKSTER_CONF_PATH': str(config_file)})

        assert get_config() is get_config()
