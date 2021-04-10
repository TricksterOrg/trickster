"""Functionality for handling configuration."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from trickster.sys import get_env
from trickster.validation import validate_json


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

    def __init__(
        self,
        internal_prefix: Optional[str] = None,
        port: Optional[int] = None,
        routes_path: Optional[str] = None
    ):
        self._internal_prefix = internal_prefix
        self._port = port
        self._routes_path = routes_path

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

    @property
    def ROUTES_PATH(self) -> Optional[Path]:  # noqa: N802
        """Get path to json file containing default routes."""
        if str_path := self._coalesce(self._routes_path, get_env('TRICKSTER_ROUTES')):
            return Path(str_path)
        return None

    @property
    def DEFAULT_ROUTES(self) -> List[Dict[str, Any]]:
        """Get default routes."""
        if path := self.ROUTES_PATH:
            with path.open() as json_file:
                routes = json.load(json_file)
                self._validate_routes(routes)
                return routes
        return []

    def _validate_routes(self, routes: List[Dict[str, Any]]) -> None:
        """Validate default routes."""
        for route in routes:
            validate_json(route, 'route.schema.json')
