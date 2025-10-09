"""
Logging configuration for OpenHeavy application.
Provides structured logging with different formatters and handlers.
"""
import logging
import logging.config
import sys
from typing import Dict, Any, Optional
from pathlib import Path
from config.settings import get_settings


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """
    Set up application logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format (json, text)
        log_file: Optional log file path
    """
    settings = get_settings()
    
    # Use provided values or fall back to settings
    log_level = log_level or settings.LOG_LEVEL
    log_format = log_format or settings.LOG_FORMAT
    
    # Create logging configuration
    config = create_logging_config(log_level, log_format, log_file)
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log configuration success
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={log_level}, format={log_format}")


def create_logging_config(
    log_level: str,
    log_format: str,
    log_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create logging configuration dictionary.
    
    Args:
        log_level: Logging level
        log_format: Log format (json, text)
        log_file: Optional log file path
        
    Returns:
        Logging configuration dictionary
    """
    # Determine formatter based on format preference
    if log_format.lower() == "json":
        formatter_name = "json"
    else:
        formatter_name = "detailed"
    
    # Base configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(levelname)s - %(name)s - %(message)s"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": "src.log_config.formatters.JSONFormatter"
            },
            "colored": {
                "()": "src.log_config.formatters.ColoredFormatter",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "colored" if sys.stdout.isatty() else formatter_name,
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            # OpenHeavy application loggers
            "src": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "config": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            # Third-party library loggers
            "werkzeug": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "socketio": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "engineio": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "openai": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "httpx": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "urllib3": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["console"]
        }
    }
    
    # Add file handler if log file specified
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "json",  # Always use JSON for file logs
            "filename": str(log_file),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8"
        }
        
        # Add file handler to all loggers
        for logger_config in config["loggers"].values():
            logger_config["handlers"].append("file")
        
        config["root"]["handlers"].append("file")
    
    return config


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def configure_flask_logging(app) -> None:
    """
    Configure Flask application logging.
    
    Args:
        app: Flask application instance
    """
    # Disable Flask's default logging setup
    app.logger.handlers.clear()
    
    # Use our logging configuration
    app.logger.propagate = True
    
    # Set appropriate log level
    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    app.logger.setLevel(log_level)


def log_application_startup() -> None:
    """Log application startup information"""
    logger = get_logger(__name__)
    settings = get_settings()
    
    logger.info("=" * 50)
    logger.info("OpenHeavy Application Starting")
    logger.info("=" * 50)
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    logger.info(f"Log Format: {settings.LOG_FORMAT}")
    logger.info(f"Flask Port: {settings.FLASK_PORT}")
    logger.info(f"Flask Debug: {settings.FLASK_DEBUG}")
    logger.info("=" * 50)


def log_application_shutdown() -> None:
    """Log application shutdown information"""
    logger = get_logger(__name__)
    
    logger.info("=" * 50)
    logger.info("OpenHeavy Application Shutting Down")
    logger.info("=" * 50)


# Convenience functions for common logging patterns

def log_request_start(request_id: str, endpoint: str, method: str = "POST") -> None:
    """Log request start"""
    logger = get_logger("src.api")
    logger.info(f"Request started", extra={
        "request_id": request_id,
        "endpoint": endpoint,
        "method": method,
        "event": "request_start"
    })


def log_request_end(request_id: str, status_code: int, duration: float) -> None:
    """Log request completion"""
    logger = get_logger("src.api")
    logger.info(f"Request completed", extra={
        "request_id": request_id,
        "status_code": status_code,
        "duration_ms": round(duration * 1000, 2),
        "event": "request_end"
    })


def log_agent_start(agent_id: str, user_request: str) -> None:
    """Log agent execution start"""
    logger = get_logger("src.core.agent")
    logger.info(f"Agent execution started", extra={
        "agent_id": agent_id,
        "request_length": len(user_request),
        "event": "agent_start"
    })


def log_agent_end(agent_id: str, success: bool, duration: float, steps: int) -> None:
    """Log agent execution completion"""
    logger = get_logger("src.core.agent")
    logger.info(f"Agent execution completed", extra={
        "agent_id": agent_id,
        "success": success,
        "duration_s": round(duration, 2),
        "steps_completed": steps,
        "event": "agent_end"
    })


def log_tool_execution(tool_name: str, success: bool, duration: float) -> None:
    """Log tool execution"""
    logger = get_logger("src.tools")
    logger.debug(f"Tool executed", extra={
        "tool_name": tool_name,
        "success": success,
        "duration_ms": round(duration * 1000, 2),
        "event": "tool_execution"
    })


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: Dict[str, Any]
) -> None:
    """
    Log error with additional context.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context information
    """
    logger.error(f"Error occurred: {str(error)}", extra={
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "context": context,
        "event": "error"
    }, exc_info=True)