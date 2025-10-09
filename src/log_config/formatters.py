"""
Custom logging formatters for OpenHeavy application.
Provides JSON and colored console formatters.
"""
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Outputs log records as JSON objects for easy parsing.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted log string
        """
        # Base log data
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add thread and process info if available
        if hasattr(record, 'thread') and record.thread:
            log_data["thread_id"] = record.thread
        
        if hasattr(record, 'process') and record.process:
            log_data["process_id"] = record.process
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from the record
        extra_fields = self._extract_extra_fields(record)
        if extra_fields:
            log_data.update(extra_fields)
        
        # Add stack info if present
        if record.stack_info:
            log_data["stack_info"] = record.stack_info
        
        try:
            return json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))
        except (TypeError, ValueError) as e:
            # Fallback to simple format if JSON serialization fails
            return f"JSON_FORMAT_ERROR: {str(e)} - Original message: {record.getMessage()}"
    
    def _extract_extra_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """
        Extract extra fields from log record.
        
        Args:
            record: Log record
            
        Returns:
            Dictionary of extra fields
        """
        # Standard fields that should not be included as extra
        standard_fields = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
            'thread', 'threadName', 'processName', 'process', 'getMessage',
            'exc_info', 'exc_text', 'stack_info', 'message'
        }
        
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in standard_fields and not key.startswith('_'):
                # Ensure value is JSON serializable
                try:
                    json.dumps(value)
                    extra_fields[key] = value
                except (TypeError, ValueError):
                    # Convert non-serializable values to string
                    extra_fields[key] = str(value)
        
        return extra_fields


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability.
    Uses ANSI color codes for different log levels.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = self._should_use_colors()
    
    def _should_use_colors(self) -> bool:
        """
        Determine if colors should be used.
        
        Returns:
            True if colors should be used
        """
        # Check if output is a TTY and colors are supported
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False
        
        # Check environment variables
        import os
        if os.getenv('NO_COLOR'):
            return False
        
        if os.getenv('FORCE_COLOR'):
            return True
        
        # Check if running on Windows and colors are supported
        if sys.platform == 'win32':
            try:
                import colorama
                colorama.init()
                return True
            except ImportError:
                return False
        
        return True
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors.
        
        Args:
            record: Log record to format
            
        Returns:
            Colored formatted log string
        """
        # Format the message using parent formatter
        message = super().format(record)
        
        if not self.use_colors:
            return message
        
        # Get color for log level
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Apply color to the entire message
        if color:
            return f"{color}{message}{reset}"
        
        return message
    
    def formatException(self, ei) -> str:
        """
        Format exception with colors.
        
        Args:
            ei: Exception info
            
        Returns:
            Formatted exception string
        """
        exception_text = super().formatException(ei)
        
        if self.use_colors:
            # Color exception text in red
            color = self.COLORS['ERROR']
            reset = self.COLORS['RESET']
            return f"{color}{exception_text}{reset}"
        
        return exception_text


class CompactFormatter(logging.Formatter):
    """
    Compact formatter for development environments.
    Provides concise log output with essential information.
    """
    
    def __init__(self, *args, **kwargs):
        # Use a compact format by default
        if not args and 'fmt' not in kwargs:
            kwargs['fmt'] = '%(levelname)s %(name)s: %(message)s'
        super().__init__(*args, **kwargs)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record in compact format.
        
        Args:
            record: Log record to format
            
        Returns:
            Compact formatted log string
        """
        # Shorten logger names for readability
        original_name = record.name
        if record.name.startswith('src.'):
            record.name = record.name[4:]  # Remove 'src.' prefix
        
        # Format the message
        message = super().format(record)
        
        # Restore original name
        record.name = original_name
        
        return message


class ContextFormatter(logging.Formatter):
    """
    Context-aware formatter that includes request/session context.
    Useful for tracking requests across the application.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with context information.
        
        Args:
            record: Log record to format
            
        Returns:
            Context-aware formatted log string
        """
        # Add context information if available
        context_parts = []
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            context_parts.append(f"req:{record.request_id[:8]}")
        
        # Add agent ID if available
        if hasattr(record, 'agent_id'):
            context_parts.append(f"agent:{record.agent_id}")
        
        # Add user ID if available
        if hasattr(record, 'user_id'):
            context_parts.append(f"user:{record.user_id}")
        
        # Prepend context to message if any context is available
        if context_parts:
            context_str = f"[{' '.join(context_parts)}] "
            original_msg = record.getMessage()
            record.msg = f"{context_str}{original_msg}"
            record.args = ()
        
        return super().format(record)


def create_formatter(
    formatter_type: str,
    format_string: Optional[str] = None,
    date_format: Optional[str] = None
) -> logging.Formatter:
    """
    Factory function to create formatters.
    
    Args:
        formatter_type: Type of formatter (json, colored, compact, context)
        format_string: Optional format string
        date_format: Optional date format
        
    Returns:
        Formatter instance
    """
    kwargs = {}
    if format_string:
        kwargs['fmt'] = format_string
    if date_format:
        kwargs['datefmt'] = date_format
    
    if formatter_type.lower() == 'json':
        return JSONFormatter(**kwargs)
    elif formatter_type.lower() == 'colored':
        return ColoredFormatter(**kwargs)
    elif formatter_type.lower() == 'compact':
        return CompactFormatter(**kwargs)
    elif formatter_type.lower() == 'context':
        return ContextFormatter(**kwargs)
    else:
        # Default to standard formatter
        return logging.Formatter(**kwargs)