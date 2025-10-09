"""
Retry utilities with exponential backoff.
Provides decorators and functions for retrying operations.
"""
import time
import random
from typing import Callable, Any, Optional, Type, Union, Tuple
from functools import wraps
import logging


logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        exceptions: Exception types to retry on
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {str(e)}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt + 1}, "
                        f"retrying in {delay:.2f}s: {str(e)}"
                    )
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def retry_operation(
    operation: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    operation_name: Optional[str] = None
) -> Any:
    """
    Retry an operation with exponential backoff.
    
    Args:
        operation: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        exceptions: Exception types to retry on
        operation_name: Name for logging (defaults to function name)
        
    Returns:
        Result of the operation
        
    Raises:
        Last exception if all retries fail
    """
    name = operation_name or getattr(operation, '__name__', 'operation')
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except exceptions as e:
            last_exception = e
            
            if attempt == max_retries:
                logger.error(f"Operation {name} failed after {max_retries} retries: {str(e)}")
                raise
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            
            # Add jitter to prevent thundering herd
            if jitter:
                delay *= (0.5 + random.random() * 0.5)
            
            logger.warning(
                f"Operation {name} failed on attempt {attempt + 1}, "
                f"retrying in {delay:.2f}s: {str(e)}"
            )
            
            time.sleep(delay)
    
    # This should never be reached, but just in case
    if last_exception:
        raise last_exception


class RetryConfig:
    """Configuration class for retry operations"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.exceptions = exceptions
    
    def retry(self, func: Callable) -> Callable:
        """Apply retry logic to a function using this configuration"""
        return retry_with_backoff(
            max_retries=self.max_retries,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
            exponential_base=self.exponential_base,
            jitter=self.jitter,
            exceptions=self.exceptions
        )(func)
    
    def retry_operation(self, operation: Callable, operation_name: Optional[str] = None) -> Any:
        """Retry an operation using this configuration"""
        return retry_operation(
            operation=operation,
            max_retries=self.max_retries,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
            exponential_base=self.exponential_base,
            jitter=self.jitter,
            exceptions=self.exceptions,
            operation_name=operation_name
        )


# Predefined retry configurations for common scenarios
DEFAULT_RETRY = RetryConfig()

NETWORK_RETRY = RetryConfig(
    max_retries=5,
    base_delay=0.5,
    max_delay=30.0,
    exceptions=(ConnectionError, TimeoutError)
)

API_RETRY = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=60.0,
    exceptions=(ConnectionError, TimeoutError, Exception)
)

FAST_RETRY = RetryConfig(
    max_retries=2,
    base_delay=0.1,
    max_delay=1.0,
    exponential_base=1.5
)