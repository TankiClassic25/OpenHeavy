"""
Base exception classes for OpenHeavy application.
Provides a foundation for all custom exceptions with consistent error handling.
"""
from typing import Optional, Dict, Any
import traceback


class BaseOpenHeavyException(Exception):
    """
    Base exception class for all OpenHeavy application errors.
    Provides consistent error handling and logging capabilities.
    """
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize the base exception.
        
        Args:
            message: Human-readable error message
            details: Additional error details and context
            error_code: Unique error code for programmatic handling
            cause: Original exception that caused this error
        """
        self.message = message
        self.details = details or {}
        self.error_code = error_code or self.__class__.__name__
        self.cause = cause
        
        # Store traceback for debugging
        self.traceback_str = traceback.format_exc()
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for serialization.
        
        Returns:
            Dictionary representation of the exception
        """
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None
        }
    
    def __str__(self) -> str:
        """String representation of the exception"""
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging"""
        return (
            f"{self.__class__.__name__}("
            f"message='{self.message}', "
            f"error_code='{self.error_code}', "
            f"details={self.details}"
            f")"
        )


class ConfigurationError(BaseOpenHeavyException):
    """
    Exception raised for configuration-related errors.
    Used when there are issues with application settings or environment.
    """
    
    def __init__(
        self, 
        message: str, 
        config_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_key: Configuration key that caused the error
            **kwargs: Additional arguments for BaseOpenHeavyException
        """
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "CONFIG_ERROR")
        
        super().__init__(message, **kwargs)


class ValidationError(BaseOpenHeavyException):
    """
    Exception raised for data validation errors.
    Used when input data doesn't meet expected format or constraints.
    """
    
    def __init__(
        self, 
        message: str, 
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        **kwargs
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field_name: Name of the field that failed validation
            field_value: Value that failed validation
            **kwargs: Additional arguments for BaseOpenHeavyException
        """
        details = kwargs.get("details", {})
        if field_name:
            details["field_name"] = field_name
        if field_value is not None:
            details["field_value"] = str(field_value)
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "VALIDATION_ERROR")
        
        super().__init__(message, **kwargs)


class ExternalServiceError(BaseOpenHeavyException):
    """
    Exception raised when external services fail or are unavailable.
    Used for API calls, database connections, etc.
    """
    
    def __init__(
        self, 
        message: str, 
        service_name: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize external service error.
        
        Args:
            message: Error message
            service_name: Name of the external service
            status_code: HTTP status code if applicable
            **kwargs: Additional arguments for BaseOpenHeavyException
        """
        details = kwargs.get("details", {})
        if service_name:
            details["service_name"] = service_name
        if status_code:
            details["status_code"] = status_code
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "EXTERNAL_SERVICE_ERROR")
        
        super().__init__(message, **kwargs)


class TimeoutError(BaseOpenHeavyException):
    """
    Exception raised when operations exceed their timeout limits.
    """
    
    def __init__(
        self, 
        message: str, 
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize timeout error.
        
        Args:
            message: Error message
            timeout_seconds: Timeout duration that was exceeded
            operation: Name of the operation that timed out
            **kwargs: Additional arguments for BaseOpenHeavyException
        """
        details = kwargs.get("details", {})
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "TIMEOUT_ERROR")
        
        super().__init__(message, **kwargs)