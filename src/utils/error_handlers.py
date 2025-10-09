"""
Global error handlers for Flask and WebSocket operations.
Provides consistent error handling and user-friendly error responses.
"""
import logging
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from src.exceptions.base import BaseOpenHeavyException
from src.models.events import ErrorEvent


logger = logging.getLogger(__name__)


def register_flask_error_handlers(app: Flask) -> None:
    """
    Register global error handlers for Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(BaseOpenHeavyException)
    def handle_openheavy_exception(error: BaseOpenHeavyException) -> tuple:
        """
        Handle custom OpenHeavy exceptions.
        
        Args:
            error: OpenHeavy exception instance
            
        Returns:
            JSON error response with appropriate status code
        """
        logger.error(
            f"OpenHeavy error: {error.error_code} - {error.message}",
            extra={
                "error_code": error.error_code,
                "error_type": error.__class__.__name__,
                "details": error.details,
                "request_path": request.path if request else None,
                "request_method": request.method if request else None
            }
        )
        
        response_data = {
            "error": True,
            "error_code": error.error_code,
            "message": error.message,
            "type": error.__class__.__name__
        }
        
        # Include details in development mode only
        if app.debug and error.details:
            response_data["details"] = error.details
        
        # Determine appropriate HTTP status code
        status_code = _get_status_code_for_exception(error)
        
        return jsonify(response_data), status_code
    
    @app.errorhandler(ValueError)
    def handle_value_error(error: ValueError) -> tuple:
        """
        Handle ValueError exceptions.
        
        Args:
            error: ValueError instance
            
        Returns:
            JSON error response
        """
        logger.warning(f"Value error: {str(error)}")
        
        return jsonify({
            "error": True,
            "error_code": "INVALID_INPUT",
            "message": "Invalid input provided",
            "type": "ValueError"
        }), 400
    
    @app.errorhandler(KeyError)
    def handle_key_error(error: KeyError) -> tuple:
        """
        Handle KeyError exceptions.
        
        Args:
            error: KeyError instance
            
        Returns:
            JSON error response
        """
        logger.warning(f"Key error: {str(error)}")
        
        return jsonify({
            "error": True,
            "error_code": "MISSING_FIELD",
            "message": f"Required field missing: {str(error)}",
            "type": "KeyError"
        }), 400
    
    @app.errorhandler(404)
    def handle_not_found(error) -> tuple:
        """
        Handle 404 Not Found errors.
        
        Args:
            error: HTTP error instance
            
        Returns:
            JSON error response
        """
        return jsonify({
            "error": True,
            "error_code": "NOT_FOUND",
            "message": "The requested resource was not found",
            "type": "NotFound"
        }), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error) -> tuple:
        """
        Handle 500 Internal Server Error.
        
        Args:
            error: HTTP error instance
            
        Returns:
            JSON error response
        """
        logger.error(f"Internal server error: {str(error)}")
        
        return jsonify({
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "An internal server error occurred",
            "type": "InternalServerError"
        }), 500
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error: Exception) -> tuple:
        """
        Handle any unhandled exceptions.
        
        Args:
            error: Exception instance
            
        Returns:
            JSON error response
        """
        logger.error(
            f"Unhandled exception: {error.__class__.__name__} - {str(error)}",
            exc_info=True
        )
        
        # Don't expose internal error details in production
        if app.debug:
            message = str(error)
        else:
            message = "An unexpected error occurred"
        
        return jsonify({
            "error": True,
            "error_code": "UNEXPECTED_ERROR",
            "message": message,
            "type": error.__class__.__name__
        }), 500


def register_socketio_error_handlers(socketio: SocketIO) -> None:
    """
    Register global error handlers for SocketIO events.
    
    Args:
        socketio: SocketIO instance
    """
    
    @socketio.on_error_default
    def default_error_handler(e):
        """
        Default error handler for SocketIO events.
        
        Args:
            e: Exception that occurred
        """
        logger.error(f"SocketIO error: {e.__class__.__name__} - {str(e)}", exc_info=True)
        
        # Create error event
        error_event = ErrorEvent(
            error_code="WEBSOCKET_ERROR",
            error_message=str(e),
            details={"error_type": e.__class__.__name__}
        )
        
        # Emit error to client
        emit('error', error_event.dict())
    

        
        emit('error', error_event.dict())


def _get_status_code_for_exception(error: BaseOpenHeavyException) -> int:
    """
    Determine appropriate HTTP status code for OpenHeavy exceptions.
    
    Args:
        error: OpenHeavy exception
        
    Returns:
        HTTP status code
    """
    from src.exceptions.agent import (
        AgentConfigurationError, PlanningError, ExecutionError,
        AgentTimeoutError, MaxRetriesExceededError
    )
    from src.exceptions.tool import (
        ToolNotFoundError, ToolParameterError, ToolDisabledError,
        ToolConfigurationError
    )
    from src.exceptions.base import (
        ConfigurationError, ValidationError, ExternalServiceError,
        TimeoutError
    )
    
    # Map exception types to HTTP status codes
    status_map = {
        # 400 Bad Request
        ValidationError: 400,
        ToolParameterError: 400,
        PlanningError: 400,
        
        # 404 Not Found
        ToolNotFoundError: 404,
        
        # 409 Conflict
        ToolDisabledError: 409,
        
        # 422 Unprocessable Entity
        ExecutionError: 422,
        
        # 500 Internal Server Error
        ConfigurationError: 500,
        AgentConfigurationError: 500,
        ToolConfigurationError: 500,
        
        # 502 Bad Gateway
        ExternalServiceError: 502,
        
        # 504 Gateway Timeout
        TimeoutError: 504,
        AgentTimeoutError: 504,
        MaxRetriesExceededError: 504,
    }
    
    return status_map.get(type(error), 500)


def emit_error_to_client(
    socketio: SocketIO,
    error: Exception
) -> None:
    """
    Emit error event to WebSocket clients.
    
    Args:
        socketio: SocketIO instance
        error: Exception to emit
    """
    if isinstance(error, BaseOpenHeavyException):
        error_event = ErrorEvent(
            error_code=error.error_code,
            error_message=error.message,
            details=error.details
        )
    else:
        error_event = ErrorEvent(
            error_code="UNEXPECTED_ERROR",
            error_message=str(error),
            details={"error_type": error.__class__.__name__}
        )
    
    # Emit to all clients
    socketio.emit('error', error_event.dict())
    
    logger.info(f"Emitted error event: {error_event.error_code}")


def create_error_response(
    error: Exception,
    include_details: bool = False
) -> Dict[str, Any]:
    """
    Create standardized error response dictionary.
    
    Args:
        error: Exception to create response for
        include_details: Whether to include detailed error information
        
    Returns:
        Error response dictionary
    """
    if isinstance(error, BaseOpenHeavyException):
        response = {
            "error": True,
            "error_code": error.error_code,
            "message": error.message,
            "type": error.__class__.__name__
        }
        
        if include_details and error.details:
            response["details"] = error.details
    else:
        response = {
            "error": True,
            "error_code": "UNEXPECTED_ERROR",
            "message": str(error),
            "type": error.__class__.__name__
        }
    
    return response