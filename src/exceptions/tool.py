"""
Tool-related exception classes.
Handles errors specific to tool operations, registration, and execution.
"""
from typing import Optional, Dict, Any
from src.exceptions.base import BaseOpenHeavyException


class ToolError(BaseOpenHeavyException):
    """
    Base exception for all tool-related errors.
    Parent class for more specific tool exceptions.
    """
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize tool error.
        
        Args:
            message: Error message
            tool_name: Name of the tool that encountered the error
            **kwargs: Additional arguments for BaseOpenHeavyException
        """
        details = kwargs.get("details", {})
        if tool_name:
            details["tool_name"] = tool_name
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "TOOL_ERROR")
        
        super().__init__(message, **kwargs)


class ToolNotFoundError(ToolError):
    """
    Exception raised when a requested tool is not found or disabled.
    """
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        available_tools: Optional[list] = None,
        **kwargs
    ):
        """
        Initialize tool not found error.
        
        Args:
            message: Error message
            tool_name: Name of the tool that was not found
            available_tools: List of available tool names
            **kwargs: Additional arguments for ToolError
        """
        details = kwargs.get("details", {})
        if available_tools:
            details["available_tools"] = available_tools
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "TOOL_NOT_FOUND")
        
        super().__init__(message, tool_name=tool_name, **kwargs)


class ToolExecutionError(ToolError):
    """
    Exception raised when tool execution fails.
    """
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize tool execution error.
        
        Args:
            message: Error message
            tool_name: Name of the tool that failed
            parameters: Parameters that were passed to the tool
            **kwargs: Additional arguments for ToolError
        """
        details = kwargs.get("details", {})
        if parameters:
            # Don't include sensitive parameters in error details
            safe_params = {k: v for k, v in parameters.items() 
                          if not any(sensitive in k.lower() 
                                   for sensitive in ['key', 'token', 'password', 'secret'])}
            details["parameters"] = safe_params
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "TOOL_EXECUTION_ERROR")
        
        super().__init__(message, tool_name=tool_name, **kwargs)


class ToolRegistrationError(ToolError):
    """
    Exception raised when tool registration fails.
    """
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        tool_class: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize tool registration error.
        
        Args:
            message: Error message
            tool_name: Name of the tool that failed to register
            tool_class: Class name of the tool
            **kwargs: Additional arguments for ToolError
        """
        details = kwargs.get("details", {})
        if tool_class:
            details["tool_class"] = tool_class
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "TOOL_REGISTRATION_ERROR")
        
        super().__init__(message, tool_name=tool_name, **kwargs)


class ToolParameterError(ToolError):
    """
    Exception raised when tool parameters are invalid.
    """
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        parameter_name: Optional[str] = None,
        parameter_value: Optional[Any] = None,
        expected_type: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize tool parameter error.
        
        Args:
            message: Error message
            tool_name: Name of the tool
            parameter_name: Name of the invalid parameter
            parameter_value: Value of the invalid parameter
            expected_type: Expected parameter type
            **kwargs: Additional arguments for ToolError
        """
        details = kwargs.get("details", {})
        if parameter_name:
            details["parameter_name"] = parameter_name
        if parameter_value is not None:
            details["parameter_value"] = str(parameter_value)
        if expected_type:
            details["expected_type"] = expected_type
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "TOOL_PARAMETER_ERROR")
        
        super().__init__(message, tool_name=tool_name, **kwargs)


class ToolTimeoutError(ToolError):
    """
    Exception raised when tool execution exceeds timeout.
    """
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        **kwargs
    ):
        """
        Initialize tool timeout error.
        
        Args:
            message: Error message
            tool_name: Name of the tool that timed out
            timeout_seconds: Timeout duration that was exceeded
            **kwargs: Additional arguments for ToolError
        """
        details = kwargs.get("details", {})
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "TOOL_TIMEOUT")
        
        super().__init__(message, tool_name=tool_name, **kwargs)


class ToolDisabledError(ToolError):
    """
    Exception raised when attempting to use a disabled tool.
    """
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize tool disabled error.
        
        Args:
            message: Error message
            tool_name: Name of the disabled tool
            **kwargs: Additional arguments for ToolError
        """
        kwargs["error_code"] = kwargs.get("error_code", "TOOL_DISABLED")
        
        super().__init__(message, tool_name=tool_name, **kwargs)


class ToolConfigurationError(ToolError):
    """
    Exception raised when tool configuration is invalid.
    """
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        config_field: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize tool configuration error.
        
        Args:
            message: Error message
            tool_name: Name of the tool with invalid configuration
            config_field: Configuration field that is invalid
            **kwargs: Additional arguments for ToolError
        """
        details = kwargs.get("details", {})
        if config_field:
            details["config_field"] = config_field
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "TOOL_CONFIG_ERROR")
        
        super().__init__(message, tool_name=tool_name, **kwargs)