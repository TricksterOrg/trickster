"""Custom exceptions for API."""


class TricksterBaseError(Exception):
    """Base class for Job Matching exceptions."""

    def __init__(self, detail: str) -> None:
        self.detail = detail

    def __str__(self) -> str:  # noqa: D105
        return self.detail


class ValidationError(TricksterBaseError):
    """Indicates that given payload does not meet the expected criteria or format."""


class ResourceNotFoundError(TricksterBaseError):
    """Indicates that given resource was not found."""


class AuthenticationError(TricksterBaseError):
    """Indicates that request is not authenticated properly."""
