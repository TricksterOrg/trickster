"""Custom exceptions for API."""


class TricksterBaseError(Exception):
    """Base class for Job Matching exceptions."""

    def __str__(self) -> str:
        if self.args:
            return self.args[0]
        else:
            return str(self.__cause__)


class ValidationError(TricksterBaseError):
    """Indicates that given payload does not meet the expected criteria or format."""


class ResourceNotFoundError(TricksterBaseError):
    """Indicates that given resource was not found."""


class AuthenticationError(TricksterBaseError):
    """Indicates that request is not authenticated properly."""
