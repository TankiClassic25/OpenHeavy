"""
Tool-related Pydantic models.
Defines models for tool registration, execution, and results.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class ToolType(str, Enum):
    """Types of tools available in the system"""
    CORE = "core"          # Essential system tools
    CUSTOM = "custom"      # User-defined tools
    EXAMPLE = "example"    # Example tools for reference


class ToolStatus(str, Enum):
    """Tool availability status"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class ToolParameter(BaseModel):
    """Definition of a tool parameter"""
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, integer, etc.)")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Optional[Any] = Field(None, description="Default value if not required")


class ToolDefinition(BaseModel):
    """
    OpenAI-compatible tool definition.
    Used for registering tools with the LLM.
    """
    type: str = Field(default="function", description="Tool type (always 'function')")
    function: Dict[str, Any] = Field(..., description="Function definition")
    
    @classmethod
    def create_function_tool(
        cls,
        name: str,
        description: str,
        parameters: List[ToolParameter]
    ) -> "ToolDefinition":
        """Create a function tool definition"""
        properties = {}
        required = []
        
        for param in parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }
            if param.required:
                required.append(param.name)
        
        function_def = {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
        
        return cls(function=function_def)


class ToolExecutionRequest(BaseModel):
    """Request to execute a tool"""
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    context: Optional[Dict[str, Any]] = Field(None, description="Execution context")


class ToolExecutionResult(BaseModel):
    """Result from tool execution"""
    tool_name: str = Field(..., description="Name of the executed tool")
    success: bool = Field(..., description="Whether execution was successful")
    result: Optional[Dict[str, Any]] = Field(None, description="Tool execution result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    execution_time: float = Field(..., description="Execution time in seconds")


class ToolRegistration(BaseModel):
    """Information about a registered tool"""
    name: str = Field(..., description="Tool name")
    tool_type: ToolType = Field(..., description="Type of tool")
    status: ToolStatus = Field(default=ToolStatus.ENABLED, description="Tool status")
    description: str = Field(..., description="Tool description")
    version: str = Field(default="1.0.0", description="Tool version")
    author: Optional[str] = Field(None, description="Tool author")
    parameters: List[ToolParameter] = Field(default_factory=list, description="Tool parameters")
    
    def to_tool_definition(self) -> ToolDefinition:
        """Convert to OpenAI tool definition"""
        return ToolDefinition.create_function_tool(
            name=self.name,
            description=self.description,
            parameters=self.parameters
        )


class ToolRegistry(BaseModel):
    """Registry of all available tools"""
    tools: Dict[str, ToolRegistration] = Field(default_factory=dict, description="Registered tools")
    
    def register_tool(self, tool_registration: ToolRegistration) -> None:
        """Register a new tool"""
        self.tools[tool_registration.name] = tool_registration
    
    def get_tool(self, name: str) -> Optional[ToolRegistration]:
        """Get tool registration by name"""
        return self.tools.get(name)
    
    def get_enabled_tools(self) -> List[ToolRegistration]:
        """Get all enabled tools"""
        return [
            tool for tool in self.tools.values() 
            if tool.status == ToolStatus.ENABLED
        ]
    
    def get_tools_by_type(self, tool_type: ToolType) -> List[ToolRegistration]:
        """Get tools by type"""
        return [
            tool for tool in self.tools.values() 
            if tool.tool_type == tool_type
        ]
    
    def enable_tool(self, name: str) -> bool:
        """Enable a tool"""
        if name in self.tools:
            self.tools[name].status = ToolStatus.ENABLED
            return True
        return False
    
    def disable_tool(self, name: str) -> bool:
        """Disable a tool"""
        if name in self.tools:
            self.tools[name].status = ToolStatus.DISABLED
            return True
        return False
    
    def get_tool_definitions(self) -> List[ToolDefinition]:
        """Get OpenAI tool definitions for all enabled tools"""
        return [
            tool.to_tool_definition() 
            for tool in self.get_enabled_tools()
        ]