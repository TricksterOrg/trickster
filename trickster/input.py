"""Incomming requests."""

from __future__ import annotations

import abc

import flask
import urllib.parse

from typing import Dict, Any


HTTP_METHODS = [
    'GET',
    'HEAD',
    'POST',
    'PUT',
    'DELETE',
    'CONNECT',
    'OPTIONS',
    'TRACE',
    'PATCH'
]


class IncommingRequest(abc.ABC):
    """Incomming request that can be validated or matched against routes."""

    @abc.abstractproperty
    def method(self) -> str:
        """HTTP method."""

    @abc.abstractproperty
    def path(self) -> str:
        """Path of the request: `http://domain.com/<path>?query`."""

    @abc.abstractproperty
    def headers(self) -> Dict[str, Any]:
        """Dictionary containing header name and value."""

    @abc.abstractproperty
    def args(self) -> Dict[str, Any]:
        """Dictionary containing URL arguments."""

    @abc.abstractproperty
    def url(self) -> str:
        """Full url of the request."""

    @abc.abstractproperty
    def query_string(self) -> str:
        """Query string of the request including ?: `http://domain.com/path<?query>`."""

    @abc.abstractproperty
    def form(self) -> Dict[str, Any]:
        """Dictionary containing form data."""

    @abc.abstractproperty
    def cookies(self) -> Dict[str, Any]:
        """Dictionary containing cookies."""


class IncommingFlaskRequest(IncommingRequest):
    """Request made by calling and API endpoint."""

    def __init__(self, request: flask.Request):
        self.request = request

    @property
    def method(self) -> str:
        """HTTP method."""
        return self.request.method

    @property
    def path(self) -> str:
        """Path of the request: `http://domain.com/<path>?query`."""
        return self.request.path

    @property
    def headers(self) -> Dict[str, Any]:
        """Dictionary containing headers."""
        return {key: value for key, value in self.request.headers.items()}

    @property
    def args(self) -> Dict[str, Any]:
        """Dictionary containing URL arguments."""
        return self.request.args

    @property
    def url(self) -> str:
        """Full url of the request."""
        return self.request.url

    @property
    def query_string(self) -> str:
        """Query string of the request: `http://domain.com/path?<query>`."""
        return self.request.query_string.decode('utf-8')

    @property
    def form(self) -> Dict[str, Any]:
        """Dictionary containing form data."""
        return self.request.form

    @property
    def cookies(self) -> Dict[str, Any]:
        """Dictionary containing cookies."""
        return self.request.cookies


class IncommingTestRequest:
    """Model of a request used for testing route matching."""

    def __init__(self, base_url: str, full_path: str, method: str):
        self.url = urllib.parse.urljoin(base_url, full_path)
        self.parsed_url = urllib.parse.urlparse(self.url)
        self.method = method

    @property
    def path(self) -> str:
        """Path of the request: `http://domain.com/<path>?query`."""
        return self.parsed_url.path

    @property
    def args(self) -> Dict[str, Any]:
        """Dictionary containing URL arguments."""
        args = urllib.parse.parse_qs(self.parsed_url.query)
        parsed_args = {}
        for key, values in args.items():
            parsed_args[key] = values[0] if len(values) == 1 else values
        return parsed_args

    @property
    def query_string(self) -> str:
        """Query string of the request: `http://domain.com/path?<query>`."""
        return self.parsed_url.query

    @property
    def headers(self) -> Dict[str, Any]:
        """Dictionary containing headers. Always empty."""
        return {}

    @property
    def form(self) -> Dict[str, Any]:
        """Dictionary containing form data. Always empty."""
        return {}

    @property
    def cookies(self) -> Dict[str, Any]:
        """Dictionary containing cookies. Always empty."""
        return {}
