"""Custom exceptions for NatureOS SDK."""


class NatureOSError(Exception):
    """Base exception for NatureOS SDK errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(NatureOSError):
    """Authentication failed."""
    pass


class NotFoundError(NatureOSError):
    """Resource not found."""
    pass


class RateLimitError(NatureOSError):
    """Rate limit exceeded."""
    pass


class ServerError(NatureOSError):
    """Server error."""
    pass

