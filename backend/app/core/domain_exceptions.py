class DomainException(Exception):
    """Base domain exception for Attendance Intelligence Platform"""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class UserNotFoundError(DomainException):
    """Raised when a user is not found in the database"""
    pass

class InvalidCredentialsError(DomainException):
    """Raised when user login credentials do not match"""
    pass

class InactiveUserError(DomainException):
    """Raised when an inactive user attempts to authenticate"""
    pass

class TokenExpiredOrInvalidError(DomainException):
    """Raised when a token (JWT / Reset) is expired or malformed"""
    pass
