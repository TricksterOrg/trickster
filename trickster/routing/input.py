"""Incoming requests."""

from __future__ import annotations

import abc
import urllib.parse
from typing import Any, Dict

import flask


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


class IncomingRequest(abc.ABC):
    """Incoming request that can be validated or matched against routes."""

    @property
    @abc.abstractmethod
    def method(self) -> str:
        """HTTP method."""

    @property
    @abc.abstractmethod
    def path(self) -> str:
        """Path of the request: `http://domain.com/<path>?query`."""

    @property
    @abc.abstractmethod
    def headers(self) -> Dict[str, Any]:
        """Dictionary containing header name and value."""

    @property
    @abc.abstractmethod
    def args(self) -> Dict[str, Any]:
        """Dictionary containing URL arguments."""

    @property
    @abc.abstractmethod
    def url(self) -> str:
        """Full url of the request."""

    @property
    @abc.abstractmethod
    def query_string(self) -> str:
        """Query string of the request including ?: `http://domain.com/path<?query>`."""

    @property
    @abc.abstractmethod
    def form(self) -> Dict[str, Any]:
        """Dictionary containing form data."""

    @property
    @abc.abstractmethod
    def cookies(self) -> Dict[str, Any]:
        """Dictionary containing cookies."""

    @property
    @abc.abstractmethod
    def body(self) -> str:
        """Body of the request."""


class IncomingFlaskRequest(IncomingRequest):
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

    @property
    def body(self) -> str:
        """Body of the request."""
        return self.request.data.decode('utf-8')


class IncomingTestRequest:
    """Model of a request used for testing route matching."""

    def __init__(
        self,
        base_url: str,
        full_path: str,
        method: str,
        headers: Dict[str, str] = None,
        form: Dict[str, str] = None,
        cookies: Dict[str, str] = None,
        body: str = ''
    ):
        self.url = urllib.parse.urljoin(base_url, full_path)
        self.parsed_url = urllib.parse.urlparse(self.url)
        self.method = method
        self.headers = headers or {}
        self.form = form or {}
        self.cookies = cookies or {}
        self.body = body

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
