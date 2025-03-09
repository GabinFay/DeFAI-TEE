"""
Custom exceptions for the Kinetic SDK.
"""


class KineticError(Exception):
    """Base exception for all Kinetic SDK errors."""
    pass


class ConnectionError(KineticError):
    """Raised when there is an error connecting to the network."""
    pass


class TransactionError(KineticError):
    """Raised when there is an error with a transaction."""
    pass


class ApprovalError(KineticError):
    """Raised when there is an error approving a token."""
    pass


class InsufficientBalanceError(KineticError):
    """Raised when there is an insufficient balance for an operation."""
    pass


class TokenNotFoundError(KineticError):
    """Raised when a token is not found."""
    pass


class KTokenNotFoundError(KineticError):
    """Raised when a kToken is not found."""
    pass 