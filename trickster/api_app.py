"""Initialization of API app."""

from __future__ import annotations

from typing import Any, Optional, Tuple

from flask import Flask, jsonify

from trickster.config import Config
from trickster.endpoints import external_api, internal_api
from trickster.routing.router import Router

from werkzeug.exceptions import HTTPException


def http_error_handler(error: HTTPException) -> Tuple[Any, Optional[int]]:
    """Handler for error pages."""
    return jsonify({
        'error': error.name,
        'message': error.description
    }), error.code


class ApiApp(Flask):
    """Flask application handling API endpoints."""

    def __init__(self, config: Config) -> None:
        super().__init__(__name__)
        self.config.from_object(config)
        self.user_router = Router()
        self.load_routes()
        self._register_handlers()
        self._register_blueprints()

    def load_routes(self) -> None:
        """Load configured default routes."""
        self.user_router.reset(self.config['DEFAULT_ROUTES'])

    def _register_handlers(self) -> None:
        """Register error page handlers."""
        self.register_error_handler(HTTPException, http_error_handler)

    def _register_blueprints(self) -> None:
        """Register api endpoints."""
        self.register_blueprint(internal_api, url_prefix=self.config['INTERNAL_PREFIX'])
        self.register_blueprint(external_api, url_prefix='')

    def run(self) -> None:  # type: ignore # pragma: no cover
        """Start app.

        Run doesn't provide the full list of options of Flask on purpose.
        It violates the Liskov Substitution Principle. But this method is not
        intended for production use. It's used only for a local run using custom
        Click API which accounts for that.

        To change the configuration of the app, use `trickster.config.Config`.
        """
        super().run(port=self.config['PORT'])
