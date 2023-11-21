"""Module provides the app config and all its sub-configs."""

from __future__ import annotations

import functools
import json
import os
import pathlib

import pydantic
import pydantic_settings

from trickster import TricksterError

from typing import Any


class ConfigError(TricksterError):
    """Exception used when something went wrong with the handling of the app's configuration."""


@functools.cache
def get_config() -> Config:
    """Provide app config."""
    return Config()


class Config(pydantic_settings.BaseSettings):
    """A main app config."""

    model_config = pydantic_settings.SettingsConfigDict(env_nested_delimiter='__', env_file_encoding='utf-8')

    internal_prefix: str = '/internal'
    openapi_boostrap: pathlib.Path | None = None  # Not FilePath because we don't require the file to exist
    logging: dict[str, Any] = {'version': 1}

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[pydantic_settings.BaseSettings],
        init_settings: pydantic_settings.PydanticBaseSettingsSource,
        env_settings: pydantic_settings.PydanticBaseSettingsSource,
        dotenv_settings: pydantic_settings.PydanticBaseSettingsSource,
        file_secret_settings: pydantic_settings.PydanticBaseSettingsSource,
    ) -> tuple[pydantic_settings.PydanticBaseSettingsSource, ...]:
        """Add json config source."""
        return init_settings, env_settings, dotenv_settings, JsonConfigSettingsSource(settings_cls)


class JsonConfigSettingsSource(pydantic_settings.PydanticBaseSettingsSource):
    """A settings source class that loads variables from a JSON file."""

    config_path_var: str = 'TRICKSTER_CONF_PATH'
    default_config_file_path: str = 'config.json'

    def __init__(self, settings_cls: type[pydantic_settings.BaseSettings]):
        super().__init__(settings_cls)
        self.config_data: dict[str, Any] = self.load()

    def load(self) -> dict[str, Any]:
        """Load the config from given path."""
        config_file_path = os.getenv(self.config_path_var, self.default_config_file_path)

        try:
            with open(config_file_path, 'rt') as config_file:  # noqa PTH123
                return json.load(config_file)
        except Exception as e:
            raise ConfigError(f'Cannot load configuration file "{config_file_path}".') from e

    def get_field_value(self, field: pydantic.fields.FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        """Get a field value from the configuration data."""
        field_value = self.config_data.get(field_name)
        return field_value, field_name, False

    def __call__(self) -> dict[str, Any]:
        """Serve the configuration data."""
        return self.config_data
