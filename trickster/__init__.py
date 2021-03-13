"""Trickster is a service providing REST API configurable by REST API."""


class TricksterException(Exception):
    """Exception from Trickster."""


class RouteConfigurationError(TricksterException, ValueError):
    """Raised when route could not be configured because of value error."""


class AuthenticationError(TricksterException):
    """Exception raised when user could not be authenticated."""
