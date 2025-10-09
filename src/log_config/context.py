"""
Request context tracking for logging.
Provides request ID tracking and context propagation across the application.
"""
import uuid
import threading
from typing import Optional, Dict, Any
from contextvars import ContextVar
import logging


# Context variables for tracking request context
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
agent_id_var: ContextVar[Optional[str]] = ContextVar('agent_id', default=None)


class RequestContext:
    """
    Request context manager for tracking request-specific information.
    """
    
    def __init__(
        self,
        request_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ):
        """
        Initialize request context.
        
        Args:
            request_id: Unique request identifier
            agent_id: Agent identifier
        """
        self.request_id = request_id or self.generate_request_id()
        self.agent_id = agent_id
        
        # Store tokens for cleanup
        self._tokens = []
    
    def __enter__(self):
        """Enter context manager"""
        self._tokens.append(request_id_var.set(self.request_id))
        
        if self.agent_id:
            self._tokens.append(agent_id_var.set(self.agent_id))
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        # Reset context variables
        for token in reversed(self._tokens):
            try:
                token.var.reset(token)
            except ValueError:
                # Token was already reset, ignore
                pass
        
        self._tokens.clear()
    
    @staticmethod
    def generate_request_id() -> str:
        """
        Generate a unique request ID.
        
        Returns:
            Unique request identifier
        """
        return str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary.
        
        Returns:
            Dictionary representation of context
        """
        return {
            'request_id': self.request_id,
            'agent_id': self.agent_id
        }


class ContextualLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that automatically includes context information.
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize contextual logger adapter.
        
        Args:
            logger: Base logger instance
        """
        super().__init__(logger, {})
    
    def process(self, msg, kwargs):
        """
        Process log message and add context information.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments
            
        Returns:
            Processed message and kwargs
        """
        # Get current context
        context = get_current_context()
        
        # Add context to extra fields
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        kwargs['extra'].update(context)
        
        return msg, kwargs


# Global context functions

def get_current_context() -> Dict[str, Any]:
    """
    Get current request context.
    
    Returns:
        Dictionary with current context information
    """
    return {
        'request_id': request_id_var.get(),
        'agent_id': agent_id_var.get()
    }


def get_request_id() -> Optional[str]:
    """
    Get current request ID.
    
    Returns:
        Current request ID or None
    """
    return request_id_var.get()


def get_agent_id() -> Optional[str]:
    """
    Get current agent ID.
    
    Returns:
        Current agent ID or None
    """
    return agent_id_var.get()


def set_request_id(request_id: str) -> None:
    """
    Set request ID in current context.
    
    Args:
        request_id: Request identifier
    """
    request_id_var.set(request_id)


def set_agent_id(agent_id: str) -> None:
    """
    Set agent ID in current context.
    
    Args:
        agent_id: Agent identifier
    """
    agent_id_var.set(agent_id)





def clear_context() -> None:
    """Clear all context variables"""
    request_id_var.set(None)
    agent_id_var.set(None)


def create_contextual_logger(name: str) -> ContextualLoggerAdapter:
    """
    Create a contextual logger that automatically includes context.
    
    Args:
        name: Logger name
        
    Returns:
        Contextual logger adapter
    """
    base_logger = logging.getLogger(name)
    return ContextualLoggerAdapter(base_logger)


# Decorators for automatic context management

def with_request_context(
    request_id: Optional[str] = None,
    agent_id: Optional[str] = None
):
    """
    Decorator to automatically set request context for a function.
    
    Args:
        request_id: Request identifier
        agent_id: Agent identifier
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with RequestContext(request_id, agent_id):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def with_agent_context(agent_id: str):
    """
    Decorator to set agent context for a function.
    
    Args:
        agent_id: Agent identifier
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Preserve existing request context
            current_request_id = get_request_id()
            with RequestContext(
                request_id=current_request_id,
                agent_id=agent_id
            ):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Thread-local storage fallback for older Python versions
class ThreadLocalContext:
    """
    Thread-local context storage as fallback.
    Used when contextvars are not available.
    """
    
    def __init__(self):
        self._storage = threading.local()
    
    def get_request_id(self) -> Optional[str]:
        """Get request ID from thread-local storage"""
        return getattr(self._storage, 'request_id', None)
    
    def set_request_id(self, request_id: str) -> None:
        """Set request ID in thread-local storage"""
        self._storage.request_id = request_id
    
    def get_agent_id(self) -> Optional[str]:
        """Get agent ID from thread-local storage"""
        return getattr(self._storage, 'agent_id', None)
    
    def set_agent_id(self, agent_id: str) -> None:
        """Set agent ID in thread-local storage"""
        self._storage.agent_id = agent_id
    
    def clear(self) -> None:
        """Clear thread-local storage"""
        for attr in ['request_id', 'agent_id']:
            if hasattr(self._storage, attr):
                delattr(self._storage, attr)


# Global thread-local context instance (fallback)
_thread_local_context = ThreadLocalContext()