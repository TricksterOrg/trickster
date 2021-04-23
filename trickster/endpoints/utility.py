"""Utility API endpoints."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify


endpoints = Blueprint('utility_api', __name__)


@endpoints.route('/health', methods=['GET'])
def health() -> Response:
    """Returns internal app status."""
    return jsonify({'status': 'ok'})
