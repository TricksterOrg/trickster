"""Initialization of API app."""

from __future__ import annotations

from werkzeug.exceptions import HTTPException
from flask import Flask, jsonify

from trickster.endpoints import internal_api, external_api
from trickster.router import Router

from typing import Tuple, Any, Optional


def http_error_handler(error: HTTPException) -> Tuple[Any, Optional[int]]:
    """Handler for error pages."""
    return jsonify({
        'error': error.name,
        'message': error.description
    }), error.code


class ApiApp(Flask):
    """Flask application handling API endpoints."""

    def __init__(self) -> None:
        super().__init__(__name__)
        self.user_router = Router()
        self._register_handlers()
        self._register_blueprints()

    def _register_handlers(self) -> None:
        """Register error page handlers."""
        self.register_error_handler(HTTPException, http_error_handler)

    def _register_blueprints(self) -> None:
        """Register api endpoints."""
        self.register_blueprint(internal_api, url_prefix='/internal')
        self.register_blueprint(external_api, url_prefix='')


def run() -> None:
    """Start API app."""
    app = ApiApp()
    app.run()
