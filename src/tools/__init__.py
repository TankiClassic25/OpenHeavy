"""
Tools system initialization and auto-discovery.
Automatically registers all available tools on import.
"""
import logging
from typing import List
from src.tools.registry import get_tool_registry, ToolRegistry
from src.tools.base import BaseTool

# Import core tools
from src.tools.core.final_response import FinalResponseTool

# Import custom tools
from src.tools.custom.web_search import WebSearchTool


logger = logging.getLogger(__name__)


def register_core_tools(registry: ToolRegistry) -> None:
    """
    Register all core system tools.
    Core tools are always enabled and required for system operation.
    """
    core_tools = [
        FinalResponseTool(),
    ]
    
    for tool in core_tools:
        try:
            registry.register_tool(tool)
            logger.info(f"Registered core tool: {tool.name}")
        except Exception as e:
            logger.error(f"Failed to register core tool {tool.name}: {e}")
            # Core tools are critical - re-raise the exception
            raise


def register_custom_tools(registry: ToolRegistry) -> None:
    """
    Register all custom tools.
    Custom tools can be enabled/disabled as needed.
    """
    custom_tools = [
        WebSearchTool(enabled=True),  # Enable web search by default
    ]
    
    for tool in custom_tools:
        try:
            registry.register_tool(tool)
            logger.info(f"Registered custom tool: {tool.name} (enabled: {tool.is_enabled()})")
        except Exception as e:
            logger.error(f"Failed to register custom tool {tool.name}: {e}")
            # Custom tools are not critical - continue with others


def register_example_tools(registry: ToolRegistry) -> None:
    """
    Register example tools for demonstration purposes.
    These are typically disabled by default.
    """
    # Example tools will be added here in the future
    # For now, this is a placeholder
    pass


def initialize_tools() -> ToolRegistry:
    """
    Initialize the tool system by registering all available tools.
    
    Returns:
        Configured ToolRegistry instance
    """
    logger.info("Initializing tools system...")
    
    registry = get_tool_registry()
    
    # Clear any existing tools
    registry.clear()
    
    # Register tools in order of importance
    register_core_tools(registry)
    register_custom_tools(registry)
    register_example_tools(registry)
    
    # Log summary
    all_tools = registry.get_all_tools()
    enabled_tools = registry.get_enabled_tools()
    
    logger.info(
        f"Tools initialization complete. "
        f"Registered {len(all_tools)} tools, "
        f"{len(enabled_tools)} enabled."
    )
    
    # Log tool details
    for tool in all_tools:
        status = "enabled" if tool.is_enabled() else "disabled"
        logger.debug(f"  - {tool.name} ({tool.tool_type}): {status}")
    
    return registry


def get_available_tools() -> List[BaseTool]:
    """
    Get all available (enabled) tools.
    
    Returns:
        List of enabled tools
    """
    registry = get_tool_registry()
    return registry.get_enabled_tools()


def get_tool_by_name(name: str) -> BaseTool:
    """
    Get a specific tool by name.
    
    Args:
        name: Tool name
        
    Returns:
        Tool instance if found and enabled
        
    Raises:
        ToolNotFoundError: If tool is not found or disabled
    """
    from src.exceptions.tool import ToolNotFoundError
    
    registry = get_tool_registry()
    tool = registry.get_tool(name)
    
    if not tool:
        raise ToolNotFoundError(f"Tool '{name}' not found or disabled")
    
    return tool


# Auto-initialize tools when module is imported
# This ensures tools are available as soon as the module is loaded
try:
    _registry = initialize_tools()
    logger.info("Tools system auto-initialization successful")
except Exception as e:
    logger.error(f"Tools system auto-initialization failed: {e}")
    # Don't raise here - let the application handle initialization errors
    _registry = None


# Export commonly used functions and classes
__all__ = [
    'BaseTool',
    'ToolRegistry',
    'get_tool_registry',
    'initialize_tools',
    'get_available_tools',
    'get_tool_by_name',
    'FinalResponseTool',
    'WebSearchTool',
]