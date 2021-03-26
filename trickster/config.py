"""Functionality for handling configuration."""

from typing import Any, Optional

from trickster.sys import get_env


class Config:
    """Flask configuration class.

    To add new configuration value, add it to the Config instance either by using
    `@property` decorator, class property or define it in constructor.

    Only properties in uppercase will propagate to the app config:
    https://flask.palletsprojects.com/en/1.1.x/config/#configuring-from-files
    """

    DEBUG = False
    TESTING = False
    DEFAULT_INTERNAL_PREFIX = '/internal'
    DEFAULT_PORT = 8080

    def __init__(self, internal_prefix: Optional[str] = None, port: Optional[int] = None):
        self._internal_prefix = internal_prefix
        self._port = port

    def _coalesce(self, *values: Any) -> Any:
        """Return first value from all arguments that doesn't evaluate to None."""
        for value in values:
            if value is not None:
                return value

    @property
    def INTERNAL_PREFIX(self) -> str:  # noqa: N802
        """Get url prefix for configuration routes."""
        return self._coalesce(
            self._internal_prefix,
            get_env('TRICKSTER_INTERNAL_PREFIX'),
            self.DEFAULT_INTERNAL_PREFIX
        )

    @property
    def PORT(self) -> int:  # noqa: N802
        """Get port to which to bind."""
        return int(self._coalesce(
            self._port,
            get_env('TRICKSTER_PORT'),
            self.DEFAULT_PORT
        ))
