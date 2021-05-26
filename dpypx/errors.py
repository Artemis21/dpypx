"""Collection of errors the wrapper can raise."""


__all__ = [
    'DpypxError', 'HttpClientError', 'ServerError', 'CanvasFormatError'
]


class DpypxError(Exception):
    """Base class for DPYPX errors."""


class HttpClientError(DpypxError):
    """Exception raised when the API returns an unhandled 400 range code."""

    def __init__(self, code: int, message: str):
        """Store the code and message."""
        self.code = code
        self.message = message
        super().__init__(f'Error {code} - {message}')


class ServerError(DpypxError):
    """Exception raised when the API returns an 500 range code."""


class CanvasFormatError(DpypxError):
    """Exception raised when the canvas is badly formatted."""
