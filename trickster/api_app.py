"""Initialization of API app."""

from __future__ import annotations

from typing import Any, Optional, Tuple

from flask import Flask, jsonify

from trickster.endpoints import external_api, internal_api
from trickster.routing import Router

from werkzeug.exceptions import HTTPException


PORT = 5000
INTERNAL_PREFIX = '/internal'


def http_error_handler(error: HTTPException) -> Tuple[Any, Optional[int]]:
    """Handler for error pages."""
    return jsonify({
        'error': error.name,
        'message': error.description
    }), error.code


class ApiApp(Flask):
    """Flask application handling API endpoints."""

    def __init__(self, internal_prefix: str = INTERNAL_PREFIX) -> None:
        super().__init__(__name__)
        self.internal_prefix = internal_prefix
        self.user_router = Router()
        self._register_handlers()
        self._register_blueprints()

    def _register_handlers(self) -> None:
        """Register error page handlers."""
        self.register_error_handler(HTTPException, http_error_handler)

    def _register_blueprints(self) -> None:
        """Register api endpoints."""
        self.register_blueprint(internal_api, url_prefix=self.internal_prefix)
        self.register_blueprint(external_api, url_prefix='')
