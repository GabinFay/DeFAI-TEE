"""
Decorators for the Kinetic SDK.
"""

import functools
from typing import List, Callable, Any, TypeVar, cast

F = TypeVar('F', bound=Callable[..., Any])


def supports(versions: List[int]) -> Callable[[F], F]:
    """
    Decorator to mark methods as supported for specific versions of the protocol.
    
    Args:
        versions: List of supported versions
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'version'):
                self.version = 1  # Default version
                
            if self.version not in versions:
                raise NotImplementedError(
                    f"This method is not supported for version {self.version}. "
                    f"Supported versions: {versions}"
                )
            return func(self, *args, **kwargs)
        return cast(F, wrapper)
    return decorator


def check_approval(func: F) -> F:
    """
    Decorator to check if a token is approved before executing a transaction.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Extract token from args or kwargs
        token = None
        if len(args) > 0 and args[0] is not None:
            token = args[0]
        elif 'token' in kwargs:
            token = kwargs['token']
        elif 'input_token' in kwargs:
            token = kwargs['input_token']
            
        # Check if token needs approval
        if token and token != self.get_weth_address():
            if not self._is_approved(token):
                self.approve(token)
                
        return func(self, *args, **kwargs)
    return cast(F, wrapper) 