"""
Common validation utilities for OpenHeavy application.
Provides reusable validation functions for various data types.
"""
import re
from typing import Any, List, Dict, Optional, Union
from urllib.parse import urlparse


def is_valid_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL format is valid
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_valid_uuid(uuid_string: str) -> bool:
    """
    Validate UUID format.
    
    Args:
        uuid_string: UUID string to validate
        
    Returns:
        True if UUID format is valid
    """
    if not uuid_string or not isinstance(uuid_string, str):
        return False
    
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    return re.match(pattern, uuid_string.lower()) is not None


def is_non_empty_string(value: Any) -> bool:
    """
    Check if value is a non-empty string.
    
    Args:
        value: Value to check
        
    Returns:
        True if value is a non-empty string
    """
    return isinstance(value, str) and len(value.strip()) > 0


def is_positive_number(value: Any) -> bool:
    """
    Check if value is a positive number.
    
    Args:
        value: Value to check
        
    Returns:
        True if value is a positive number
    """
    try:
        num = float(value)
        return num > 0
    except (TypeError, ValueError):
        return False


def is_non_negative_number(value: Any) -> bool:
    """
    Check if value is a non-negative number.
    
    Args:
        value: Value to check
        
    Returns:
        True if value is a non-negative number
    """
    try:
        num = float(value)
        return num >= 0
    except (TypeError, ValueError):
        return False


def is_valid_port(port: Any) -> bool:
    """
    Check if value is a valid port number.
    
    Args:
        port: Port value to check
        
    Returns:
        True if port is valid (1-65535)
    """
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (TypeError, ValueError):
        return False


def is_valid_json(json_string: str) -> bool:
    """
    Check if string is valid JSON.
    
    Args:
        json_string: JSON string to validate
        
    Returns:
        True if string is valid JSON
    """
    if not isinstance(json_string, str):
        return False
    
    try:
        import json
        json.loads(json_string)
        return True
    except (ValueError, TypeError):
        return False


def validate_string_length(
    value: str, 
    min_length: int = 0, 
    max_length: Optional[int] = None
) -> bool:
    """
    Validate string length.
    
    Args:
        value: String to validate
        min_length: Minimum length (default: 0)
        max_length: Maximum length (optional)
        
    Returns:
        True if string length is within bounds
    """
    if not isinstance(value, str):
        return False
    
    length = len(value)
    
    if length < min_length:
        return False
    
    if max_length is not None and length > max_length:
        return False
    
    return True


def validate_number_range(
    value: Union[int, float], 
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None
) -> bool:
    """
    Validate number is within range.
    
    Args:
        value: Number to validate
        min_value: Minimum value (optional)
        max_value: Maximum value (optional)
        
    Returns:
        True if number is within range
    """
    if not isinstance(value, (int, float)):
        return False
    
    if min_value is not None and value < min_value:
        return False
    
    if max_value is not None and value > max_value:
        return False
    
    return True


def validate_list_length(
    value: List[Any], 
    min_length: int = 0, 
    max_length: Optional[int] = None
) -> bool:
    """
    Validate list length.
    
    Args:
        value: List to validate
        min_length: Minimum length (default: 0)
        max_length: Maximum length (optional)
        
    Returns:
        True if list length is within bounds
    """
    if not isinstance(value, list):
        return False
    
    length = len(value)
    
    if length < min_length:
        return False
    
    if max_length is not None and length > max_length:
        return False
    
    return True


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validate that required fields are present in data.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        List of missing field names (empty if all present)
    """
    if not isinstance(data, dict):
        return required_fields.copy()
    
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    return missing_fields


def validate_agent_id(agent_id: str) -> bool:
    """
    Validate agent ID format.
    
    Args:
        agent_id: Agent ID to validate
        
    Returns:
        True if agent ID format is valid
    """
    if not isinstance(agent_id, str):
        return False
    
    # Agent ID should be non-empty and contain only alphanumeric characters, underscores, and hyphens
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, agent_id)) and len(agent_id) > 0


def validate_tool_name(tool_name: str) -> bool:
    """
    Validate tool name format.
    
    Args:
        tool_name: Tool name to validate
        
    Returns:
        True if tool name format is valid
    """
    if not isinstance(tool_name, str):
        return False
    
    # Tool name should be lowercase with underscores
    pattern = r'^[a-z][a-z0-9_]*$'
    return bool(re.match(pattern, tool_name)) and len(tool_name) > 0


def validate_temperature(temperature: float) -> bool:
    """
    Validate LLM temperature parameter.
    
    Args:
        temperature: Temperature value to validate
        
    Returns:
        True if temperature is valid (0.0 to 2.0)
    """
    return validate_number_range(temperature, 0.0, 2.0)


def validate_top_p(top_p: float) -> bool:
    """
    Validate LLM top_p parameter.
    
    Args:
        top_p: Top_p value to validate
        
    Returns:
        True if top_p is valid (0.0 to 1.0)
    """
    return validate_number_range(top_p, 0.0, 1.0)


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string by removing potentially harmful characters.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return ""
    
    # Remove null bytes and control characters (except newlines and tabs)
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_file_path(file_path: str) -> bool:
    """
    Validate file path format (basic security check).
    
    Args:
        file_path: File path to validate
        
    Returns:
        True if file path appears safe
    """
    if not isinstance(file_path, str):
        return False
    
    # Check for path traversal attempts
    dangerous_patterns = ['../', '..\\', '/..', '\\..']
    for pattern in dangerous_patterns:
        if pattern in file_path:
            return False
    
    # Check for absolute paths (should be relative)
    if file_path.startswith('/') or (len(file_path) > 1 and file_path[1] == ':'):
        return False
    
    return True


class ValidationError(Exception):
    """Custom exception for validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


def validate_or_raise(condition: bool, message: str, field: Optional[str] = None) -> None:
    """
    Validate condition or raise ValidationError.
    
    Args:
        condition: Condition to validate
        message: Error message if validation fails
        field: Field name associated with validation
        
    Raises:
        ValidationError: If condition is False
    """
    if not condition:
        raise ValidationError(message, field)


def validate_dict_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate dictionary against a simple schema.
    
    Args:
        data: Data to validate
        schema: Schema definition with field types and requirements
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    if not isinstance(data, dict):
        errors.append("Data must be a dictionary")
        return errors
    
    for field, requirements in schema.items():
        field_type = requirements.get('type')
        required = requirements.get('required', False)
        
        if required and field not in data:
            errors.append(f"Required field '{field}' is missing")
            continue
        
        if field in data:
            value = data[field]
            
            if field_type and not isinstance(value, field_type):
                errors.append(f"Field '{field}' must be of type {field_type.__name__}")
            
            # Additional validations
            if 'min_length' in requirements and hasattr(value, '__len__'):
                if len(value) < requirements['min_length']:
                    errors.append(f"Field '{field}' must have at least {requirements['min_length']} characters")
            
            if 'max_length' in requirements and hasattr(value, '__len__'):
                if len(value) > requirements['max_length']:
                    errors.append(f"Field '{field}' must have at most {requirements['max_length']} characters")
    
    return errors