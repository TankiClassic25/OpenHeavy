"""
Agent-related exception classes.
Handles errors specific to agent operations, planning, and execution.
"""
from typing import Optional, Dict, Any
from src.exceptions.base import BaseOpenHeavyException


class AgentError(BaseOpenHeavyException):
    """
    Base exception for all agent-related errors.
    Parent class for more specific agent exceptions.
    """
    
    def __init__(
        self, 
        message: str, 
        agent_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize agent error.
        
        Args:
            message: Error message
            agent_id: ID of the agent that encountered the error
            **kwargs: Additional arguments for BaseOpenHeavyException
        """
        details = kwargs.get("details", {})
        if agent_id:
            details["agent_id"] = agent_id
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "AGENT_ERROR")
        
        super().__init__(message, **kwargs)


class PlanningError(AgentError):
    """
    Exception raised during the planning phase of agent execution.
    Occurs when agents fail to create valid execution plans.
    """
    
    def __init__(
        self, 
        message: str, 
        user_request: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize planning error.
        
        Args:
            message: Error message
            user_request: Original user request that failed planning
            **kwargs: Additional arguments for AgentError
        """
        details = kwargs.get("details", {})
        if user_request:
            details["user_request"] = user_request
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "PLANNING_ERROR")
        
        super().__init__(message, **kwargs)


class ExecutionError(AgentError):
    """
    Exception raised during the execution phase of agent operations.
    Occurs when agents fail to execute individual steps or complete plans.
    """
    
    def __init__(
        self, 
        message: str, 
        step_index: Optional[int] = None,
        step_title: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize execution error.
        
        Args:
            message: Error message
            step_index: Index of the step that failed
            step_title: Title of the step that failed
            **kwargs: Additional arguments for AgentError
        """
        details = kwargs.get("details", {})
        if step_index is not None:
            details["step_index"] = step_index
        if step_title:
            details["step_title"] = step_title
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "EXECUTION_ERROR")
        
        super().__init__(message, **kwargs)


class AgentTimeoutError(AgentError):
    """
    Exception raised when agent operations exceed timeout limits.
    """
    
    def __init__(
        self, 
        message: str, 
        timeout_seconds: Optional[float] = None,
        **kwargs
    ):
        """
        Initialize agent timeout error.
        
        Args:
            message: Error message
            timeout_seconds: Timeout that was exceeded
            **kwargs: Additional arguments for AgentError
        """
        details = kwargs.get("details", {})
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "AGENT_TIMEOUT")
        
        super().__init__(message, **kwargs)


class AgentConfigurationError(AgentError):
    """
    Exception raised when agent configuration is invalid or missing.
    """
    
    def __init__(
        self, 
        message: str, 
        config_field: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize agent configuration error.
        
        Args:
            message: Error message
            config_field: Configuration field that is invalid
            **kwargs: Additional arguments for AgentError
        """
        details = kwargs.get("details", {})
        if config_field:
            details["config_field"] = config_field
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "AGENT_CONFIG_ERROR")
        
        super().__init__(message, **kwargs)


class LLMServiceError(AgentError):
    """
    Exception raised when LLM service calls fail.
    Wraps errors from OpenAI API or other LLM providers.
    """
    
    def __init__(
        self, 
        message: str, 
        model_name: Optional[str] = None,
        api_error: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize LLM service error.
        
        Args:
            message: Error message
            model_name: Name of the model that failed
            api_error: Original API error message
            **kwargs: Additional arguments for AgentError
        """
        details = kwargs.get("details", {})
        if model_name:
            details["model_name"] = model_name
        if api_error:
            details["api_error"] = api_error
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "LLM_SERVICE_ERROR")
        
        super().__init__(message, **kwargs)


class MaxRetriesExceededError(AgentError):
    """
    Exception raised when maximum retry attempts are exceeded.
    """
    
    def __init__(
        self, 
        message: str, 
        max_retries: Optional[int] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize max retries exceeded error.
        
        Args:
            message: Error message
            max_retries: Maximum number of retries that were attempted
            operation: Operation that failed after retries
            **kwargs: Additional arguments for AgentError
        """
        details = kwargs.get("details", {})
        if max_retries is not None:
            details["max_retries"] = max_retries
        if operation:
            details["operation"] = operation
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "MAX_RETRIES_EXCEEDED")
        
        super().__init__(message, **kwargs)


class SynthesisError(AgentError):
    """
    Exception raised during answer synthesis from multiple agents.
    """
    
    def __init__(
        self, 
        message: str, 
        agent_count: Optional[int] = None,
        successful_agents: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize synthesis error.
        
        Args:
            message: Error message
            agent_count: Total number of agents
            successful_agents: Number of agents that completed successfully
            **kwargs: Additional arguments for AgentError
        """
        details = kwargs.get("details", {})
        if agent_count is not None:
            details["agent_count"] = agent_count
        if successful_agents is not None:
            details["successful_agents"] = successful_agents
        
        kwargs["details"] = details
        kwargs["error_code"] = kwargs.get("error_code", "SYNTHESIS_ERROR")
        
        super().__init__(message, **kwargs)