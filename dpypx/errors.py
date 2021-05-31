"""Collection of errors the wrapper can raise."""


__all__ = [
    'DpypxError',
    'HttpClientError',
    'RatelimitedError',
    'MethodNotAllowedError',
    'ServerError',
    'CanvasFormatError'
]


class DpypxError(Exception):
    """Base class for DPYPX errors."""


class HttpClientError(DpypxError):
    """Exception raised when the API returns a 400 range code."""

    def __init__(self, code: int, message: str):
        """Store the code and message."""
        self.code = code
        self.message = message
        super().__init__(f'Error {code} - {message}')


class RatelimitedError(HttpClientError):
    """Exception raised when the client is ratelimited (code 429).

    This should be caught by the client so consumers of the library should
    not need to handle this.
    """


class MethodNotAllowedError(HttpClientError):
    """Exception raised when the client sends the wrong HTTP method.

    This could mean that the client is buggy, but it is also raised sometimes
    during normal operation of the client (and is caught).
    """


class ServerError(DpypxError):
    """Exception raised when the API returns an 500 range code."""


class CanvasFormatError(DpypxError):
    """Exception raised when the canvas is badly formatted."""
