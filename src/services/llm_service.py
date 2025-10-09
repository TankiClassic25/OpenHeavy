"""
LLM service for handling OpenAI API interactions.
Wraps the OpenAI client with retry logic and error handling.
"""
import time
from typing import List, Dict, Any, Optional, Union, Generator
from openai import OpenAI
from src.core.interfaces import ILLMService
from src.models.agent import AgentConfig
from src.exceptions.agent import LLMServiceError, MaxRetriesExceededError
from src.utils.retry import retry_with_backoff
import logging


logger = logging.getLogger(__name__)


class LLMService(ILLMService):
    """
    Service for interacting with LLM APIs.
    Provides retry logic, error handling, and consistent interface.
    """
    
    def __init__(self, agent_config: AgentConfig):
        """
        Initialize the LLM service.
        
        Args:
            agent_config: Agent configuration containing API settings
        """
        self.config = agent_config
        self.client = OpenAI(
            base_url=agent_config.base_url,
            api_key=agent_config.api_key
        )
        self.default_model = agent_config.model
        self.max_retries = agent_config.max_retries
    
    def create_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        tool_choice: str = "auto",
        **kwargs
    ) -> Any:
        """
        Create a completion using the LLM service.
        
        Args:
            messages: Conversation messages
            tools: Available tools for the LLM
            model: Model to use (defaults to config model)
            temperature: Temperature setting
            top_p: Top-p setting
            stream: Whether to stream the response
            tool_choice: Tool choice strategy
            **kwargs: Additional parameters
            
        Returns:
            LLM completion response
            
        Raises:
            LLMServiceError: If LLM call fails
            MaxRetriesExceededError: If max retries exceeded
        """
        # Use config defaults if not specified
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.config.temperature
        top_p = top_p if top_p is not None else self.config.top_p
        
        # Prepare request parameters
        request_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream,
            **kwargs
        }
        
        # Add tools if provided
        if tools:
            request_params["tools"] = tools
            request_params["tool_choice"] = tool_choice
        
        logger.debug(f"Creating LLM completion with model {model}")
        
        try:
            return self._make_request_with_retry(request_params)
        except Exception as e:
            raise LLMServiceError(
                f"LLM completion failed: {str(e)}",
                model_name=model,
                api_error=str(e),
                cause=e
            )
    
    def create_structured_completion(
        self,
        messages: List[Dict[str, str]],
        response_format: type,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Create a structured completion with a specific response format.
        
        Args:
            messages: Conversation messages
            response_format: Pydantic model for response structure
            model: Model to use
            temperature: Temperature setting
            top_p: Top-p setting
            **kwargs: Additional parameters
            
        Returns:
            Structured LLM response
            
        Raises:
            LLMServiceError: If LLM call fails
        """
        # Use config defaults if not specified
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.config.temperature
        top_p = top_p if top_p is not None else self.config.top_p
        
        # Prepare request parameters for structured parsing
        request_params = {
            "model": model,
            "messages": messages,
            "response_format": response_format,
            "temperature": temperature,
            "top_p": top_p,
            **kwargs
        }
        
        logger.debug(f"Creating structured LLM completion with model {model}")
        
        try:
            return self._make_structured_request_with_retry(request_params)
        except Exception as e:
            raise LLMServiceError(
                f"Structured LLM completion failed: {str(e)}",
                model_name=model,
                api_error=str(e),
                cause=e
            )
    
    def create_streaming_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        **kwargs
    ) -> Generator[Any, None, None]:
        """
        Create a streaming completion.
        
        Args:
            messages: Conversation messages
            model: Model to use
            temperature: Temperature setting
            top_p: Top-p setting
            **kwargs: Additional parameters
            
        Yields:
            Streaming response chunks
            
        Raises:
            LLMServiceError: If streaming fails
        """
        try:
            response = self.create_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                top_p=top_p,
                stream=True,
                **kwargs
            )
            
            for chunk in response:
                yield chunk
                
        except Exception as e:
            raise LLMServiceError(
                f"Streaming completion failed: {str(e)}",
                model_name=model or self.default_model,
                api_error=str(e),
                cause=e
            )
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def _make_request_with_retry(self, request_params: Dict[str, Any]) -> Any:
        """
        Make LLM request with retry logic.
        
        Args:
            request_params: Request parameters
            
        Returns:
            LLM response
        """
        try:
            return self.client.chat.completions.create(**request_params)
        except Exception as e:
            logger.warning(f"LLM request failed, will retry: {str(e)}")
            raise
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def _make_structured_request_with_retry(self, request_params: Dict[str, Any]) -> Any:
        """
        Make structured LLM request with retry logic.
        
        Args:
            request_params: Request parameters
            
        Returns:
            Structured LLM response
        """
        try:
            return self.client.chat.completions.parse(**request_params)
        except Exception as e:
            logger.warning(f"Structured LLM request failed, will retry: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test if the LLM service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        try:
            response = self.create_completion(
                messages=[{"role": "user", "content": "Hello"}],
                temperature=0.1
            )
            return response is not None
        except Exception as e:
            logger.error(f"LLM service connection test failed: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the configured model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model": self.default_model,
            "base_url": self.config.base_url,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "max_retries": self.max_retries
        }
    
    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimation of token count for text.
        Uses a simple heuristic (4 characters per token on average).
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Simple heuristic: ~4 characters per token
        return len(text) // 4
    
    def validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """
        Validate message format for LLM requests.
        
        Args:
            messages: Messages to validate
            
        Returns:
            True if messages are valid
            
        Raises:
            ValueError: If messages are invalid
        """
        if not messages:
            raise ValueError("Messages cannot be empty")
        
        valid_roles = {"system", "user", "assistant", "tool"}
        
        for i, message in enumerate(messages):
            if not isinstance(message, dict):
                raise ValueError(f"Message {i} must be a dictionary")
            
            if "role" not in message:
                raise ValueError(f"Message {i} missing 'role' field")
            
            if message["role"] not in valid_roles:
                raise ValueError(f"Message {i} has invalid role: {message['role']}")
            
            if "content" not in message and message["role"] != "assistant":
                raise ValueError(f"Message {i} missing 'content' field")
        
        return True