"""Trickster is a service providing REST API configurable by REST API."""


class TricksterException(Exception):
    """Exception from Trickster."""


class RouteConfigurationError(TricksterException, ValueError):
    """Raised when route could not be configured because of value error."""

    http_code: int = 400


class DuplicateRouteError(RouteConfigurationError):
    """Raised when route could not be configured because there is a duplicatit in ids."""

    http_code: int = 409


class MissingRouteError(RouteConfigurationError):
    """Raised when route could not be configured because it doesn't exist."""

    http_code: int = 404


class AuthenticationError(TricksterException):
    """Exception raised when user could not be authenticated."""
