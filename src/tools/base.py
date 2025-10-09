"""
Base tool classes and interfaces.
Provides the foundation for all tools in the system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from src.models.tool import ToolParameter, ToolRegistration, ToolType, ToolStatus


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    All tools must inherit from this class and implement the required methods.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize the tool.
        
        Args:
            enabled: Whether the tool is enabled by default
        """
        self.enabled = enabled
        self._registration: Optional[ToolRegistration] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name - must be unique across all tools"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does"""
        pass
    
    @property
    @abstractmethod
    def tool_type(self) -> ToolType:
        """Type of tool (core, custom, example)"""
        pass
    
    @property
    def version(self) -> str:
        """Tool version"""
        return "1.0.0"
    
    @property
    def author(self) -> Optional[str]:
        """Tool author"""
        return None
    
    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """
        Get the parameters this tool accepts.
        
        Returns:
            List of ToolParameter objects defining the tool's interface
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Dictionary containing the tool's result
            
        Raises:
            ToolExecutionError: If tool execution fails
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if the tool is enabled"""
        return self.enabled
    
    def enable(self) -> None:
        """Enable the tool"""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable the tool"""
        self.enabled = False
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate that the provided parameters match the tool's requirements.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            True if parameters are valid
            
        Raises:
            ValueError: If parameters are invalid
        """
        tool_params = {param.name: param for param in self.get_parameters()}
        
        # Check required parameters
        for param in self.get_parameters():
            if param.required and param.name not in parameters:
                raise ValueError(f"Required parameter '{param.name}' is missing")
        
        # Check for unknown parameters
        for param_name in parameters:
            if param_name not in tool_params:
                raise ValueError(f"Unknown parameter '{param_name}'")
        
        return True
    
    def get_registration(self) -> ToolRegistration:
        """
        Get the tool registration information.
        
        Returns:
            ToolRegistration object for this tool
        """
        if self._registration is None:
            self._registration = ToolRegistration(
                name=self.name,
                tool_type=self.tool_type,
                status=ToolStatus.ENABLED if self.enabled else ToolStatus.DISABLED,
                description=self.description,
                version=self.version,
                author=self.author,
                parameters=self.get_parameters()
            )
        return self._registration
    
    def __str__(self) -> str:
        """String representation of the tool"""
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the tool"""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"type={self.tool_type}, "
            f"enabled={self.enabled}, "
            f"version='{self.version}'"
            f")"
        )