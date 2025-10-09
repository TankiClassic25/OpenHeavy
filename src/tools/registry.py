"""
Tool registry for managing and discovering tools.
Provides centralized tool management with enable/disable functionality.
"""
from typing import Dict, List, Optional, Type, Any
import logging
from src.tools.base import BaseTool
from src.models.tool import ToolRegistration, ToolType, ToolStatus, ToolDefinition
from src.exceptions.tool import ToolNotFoundError, ToolRegistrationError


logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for all tools in the system.
    Manages tool registration, discovery, and lifecycle.
    """
    
    def __init__(self):
        """Initialize the tool registry"""
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool instance in the registry.
        
        Args:
            tool: Tool instance to register
            
        Raises:
            ToolRegistrationError: If tool registration fails
        """
        try:
            if not isinstance(tool, BaseTool):
                raise ToolRegistrationError(
                    f"Tool must inherit from BaseTool, got {type(tool)}"
                )
            
            if tool.name in self._tools:
                logger.warning(f"Tool '{tool.name}' is already registered, replacing...")
            
            self._tools[tool.name] = tool
            self._tool_classes[tool.name] = type(tool)
            
            logger.info(f"Registered tool: {tool.name} ({tool.tool_type})")
            
        except Exception as e:
            raise ToolRegistrationError(f"Failed to register tool '{tool.name}': {str(e)}")
    
    def register_tool_class(self, tool_class: Type[BaseTool], **kwargs) -> None:
        """
        Register a tool class and instantiate it.
        
        Args:
            tool_class: Tool class to register
            **kwargs: Arguments to pass to tool constructor
            
        Raises:
            ToolRegistrationError: If tool registration fails
        """
        try:
            tool_instance = tool_class(**kwargs)
            self.register_tool(tool_instance)
        except Exception as e:
            raise ToolRegistrationError(
                f"Failed to register tool class '{tool_class.__name__}': {str(e)}"
            )
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name if it's enabled.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance if found and enabled, None otherwise
        """
        tool = self._tools.get(name)
        if tool and tool.is_enabled():
            return tool
        return None
    
    def get_tool_force(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name regardless of enabled status.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance if found, None otherwise
        """
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools"""
        return list(self._tools.values())
    
    def get_enabled_tools(self) -> List[BaseTool]:
        """Get all enabled tools"""
        return [tool for tool in self._tools.values() if tool.is_enabled()]
    
    def get_tools_by_type(self, tool_type: ToolType) -> List[BaseTool]:
        """
        Get all tools of a specific type.
        
        Args:
            tool_type: Type of tools to retrieve
            
        Returns:
            List of tools of the specified type
        """
        return [
            tool for tool in self._tools.values() 
            if tool.tool_type == tool_type
        ]
    
    def get_enabled_tools_by_type(self, tool_type: ToolType) -> List[BaseTool]:
        """
        Get all enabled tools of a specific type.
        
        Args:
            tool_type: Type of tools to retrieve
            
        Returns:
            List of enabled tools of the specified type
        """
        return [
            tool for tool in self.get_tools_by_type(tool_type) 
            if tool.is_enabled()
        ]
    
    def enable_tool(self, name: str) -> bool:
        """
        Enable a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            True if tool was enabled, False if not found
        """
        tool = self._tools.get(name)
        if tool:
            tool.enable()
            logger.info(f"Enabled tool: {name}")
            return True
        return False
    
    def disable_tool(self, name: str) -> bool:
        """
        Disable a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            True if tool was disabled, False if not found
        """
        tool = self._tools.get(name)
        if tool:
            tool.disable()
            logger.info(f"Disabled tool: {name}")
            return True
        return False
    
    def is_tool_registered(self, name: str) -> bool:
        """Check if a tool is registered"""
        return name in self._tools
    
    def is_tool_enabled(self, name: str) -> bool:
        """Check if a tool is registered and enabled"""
        tool = self._tools.get(name)
        return tool is not None and tool.is_enabled()
    
    def get_tool_registrations(self) -> List[ToolRegistration]:
        """Get registration information for all tools"""
        return [tool.get_registration() for tool in self._tools.values()]
    
    def get_enabled_tool_registrations(self) -> List[ToolRegistration]:
        """Get registration information for enabled tools only"""
        return [tool.get_registration() for tool in self.get_enabled_tools()]
    
    def get_tool_definitions(self) -> List[ToolDefinition]:
        """
        Get OpenAI-compatible tool definitions for all enabled tools.
        
        Returns:
            List of tool definitions for LLM integration
        """
        definitions = []
        for tool in self.get_enabled_tools():
            try:
                registration = tool.get_registration()
                definition = registration.to_tool_definition()
                definitions.append(definition)
            except Exception as e:
                logger.error(f"Failed to create definition for tool '{tool.name}': {e}")
        
        return definitions
    
    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            ToolNotFoundError: If tool is not found or disabled
        """
        tool = self.get_tool(name)
        if not tool:
            if name in self._tools:
                raise ToolNotFoundError(f"Tool '{name}' is disabled")
            else:
                raise ToolNotFoundError(f"Tool '{name}' not found")
        
        # Validate parameters
        tool.validate_parameters(kwargs)
        
        # Execute tool
        return tool.execute(**kwargs)
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get a summary of all registered tools.
        
        Returns:
            Dictionary with tool information
        """
        tools_info = {}
        for name, tool in self._tools.items():
            tools_info[name] = {
                "type": tool.tool_type,
                "enabled": tool.is_enabled(),
                "description": tool.description,
                "version": tool.version,
                "author": tool.author,
                "parameters": len(tool.get_parameters())
            }
        return tools_info
    
    def clear(self) -> None:
        """Clear all registered tools"""
        self._tools.clear()
        self._tool_classes.clear()
        logger.info("Cleared all registered tools")


# Global tool registry instance
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.
    
    Returns:
        Global ToolRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(tool: BaseTool) -> None:
    """
    Register a tool in the global registry.
    
    Args:
        tool: Tool instance to register
    """
    registry = get_tool_registry()
    registry.register_tool(tool)


def get_tool(name: str) -> Optional[BaseTool]:
    """
    Get a tool from the global registry.
    
    Args:
        name: Tool name
        
    Returns:
        Tool instance if found and enabled
    """
    registry = get_tool_registry()
    return registry.get_tool(name)