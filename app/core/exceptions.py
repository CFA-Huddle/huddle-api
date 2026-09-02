class DatabaseError(Exception):
    """Raised when a database operation fails."""


class S3UploadError(Exception):
    """Raised when an S3 upload operation fails."""


class AuthClientError(Exception):
    """Raised when an auth client (i.e. Cognito client) operation fails."""


class NotFoundError(Exception):
    """Raised when a requested resource is not found."""


class AlreadyExistsError(Exception):
    """Raised when creating a resource that already exists."""


class PermissionDeniedError(Exception):
    """Raised when a user is not authorized to perform an action."""


class UserCreationError(Exception):
    """Raised when an error occurs when creating a user."""


class InvalidListModificationError(Exception):
    """Raised when a list is modified incorrectly. Used primarily for situations where reordering/editing items is allowed but adding/deleting items is not"""
