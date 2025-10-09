"""
Final response tool - core system tool.
This tool is required by all agents to return their final results.
It cannot be disabled as it's essential for agent operation.
"""
from typing import Dict, Any, List
from src.tools.base import BaseTool
from src.models.tool import ToolParameter, ToolType


class FinalResponseTool(BaseTool):
    """
    Core tool for returning final or intermediate results from subagents.
    This tool is always enabled and cannot be disabled.
    """
    
    def __init__(self):
        """Initialize the final response tool - always enabled"""
        super().__init__(enabled=True)
    
    @property
    def name(self) -> str:
        """Tool name"""
        return "final_response"
    
    @property
    def description(self) -> str:
        """Tool description"""
        return "Return the final or intermediate result produced by this subagent."
    
    @property
    def tool_type(self) -> ToolType:
        """Tool type - core system tool"""
        return ToolType.CORE
    
    @property
    def version(self) -> str:
        """Tool version"""
        return "1.0.0"
    
    @property
    def author(self) -> str:
        """Tool author"""
        return "OpenHeavy System"
    
    def get_parameters(self) -> List[ToolParameter]:
        """
        Get tool parameters.
        
        Returns:
            List of parameters this tool accepts
        """
        return [
            ToolParameter(
                name="content",
                type="string",
                description="Result content.",
                required=True
            )
        ]
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the final response tool.
        
        Args:
            **kwargs: Tool parameters, must include 'content'
            
        Returns:
            The content as provided by the agent
            
        Raises:
            ValueError: If content parameter is missing
        """
        # Validate parameters
        self.validate_parameters(kwargs)
        
        content = kwargs.get("content")
        
        if not content:
            raise ValueError("Content parameter cannot be empty")
        
        # Return the content directly - this matches the original behavior
        # where final_response returned the content string
        return content
    
    def disable(self) -> None:
        """
        Override disable method - this tool cannot be disabled.
        Core tools are always required for system operation.
        """
        # Log warning but don't actually disable
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Attempted to disable core tool '{self.name}'. "
            "Core tools cannot be disabled."
        )
    
    def is_enabled(self) -> bool:
        """Core tools are always enabled"""
        return True