# Custom Tools

This directory contains custom tools that extend the OpenHeavy system's capabilities. Custom tools can be enabled or disabled as needed and provide additional functionality beyond the core system tools.

## Available Custom Tools

### WebSearchTool
- **Name**: `web_search`
- **Description**: Performs web searches using SearXNG API
- **Status**: Enabled by default
- **Parameters**:
  - `query` (required): Search query string
  - `max_results` (optional): Maximum number of results to return

## Creating Custom Tools

To create a new custom tool, follow these steps:

### 1. Create Tool Class

Create a new Python file in this directory and inherit from `BaseTool`:

```python
from typing import Dict, Any, List
from src.tools.base import BaseTool
from src.models.tool import ToolParameter, ToolType

class MyCustomTool(BaseTool):
    def __init__(self, enabled: bool = True):
        super().__init__(enabled=enabled)
    
    @property
    def name(self) -> str:
        return "my_custom_tool"
    
    @property
    def description(self) -> str:
        return "Description of what my tool does"
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.CUSTOM
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="input_param",
                type="string",
                description="Description of the parameter",
                required=True
            )
        ]
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        # Validate parameters
        self.validate_parameters(kwargs)
        
        # Your tool logic here
        result = "Tool output"
        
        return {"content": result}
```

### 2. Register Tool

Add your tool to the registration in `src/tools/__init__.py`:

```python
# Import your tool
from src.tools.custom.my_custom_tool import MyCustomTool

# Add to custom_tools list in register_custom_tools()
custom_tools = [
    WebSearchTool(enabled=True),
    MyCustomTool(enabled=True),  # Add your tool here
]
```

### 3. Tool Guidelines

When creating custom tools, follow these guidelines:

#### Required Methods
- `name`: Unique tool name (lowercase, underscores allowed)
- `description`: Clear description of tool functionality
- `tool_type`: Should be `ToolType.CUSTOM` for custom tools
- `get_parameters()`: Define tool parameters with types and descriptions
- `execute(**kwargs)`: Implement tool logic and return results

#### Best Practices
- Always validate parameters using `self.validate_parameters(kwargs)`
- Return results in a consistent format (usually `{"content": "result"}`)
- Handle errors gracefully and return meaningful error messages
- Add comprehensive docstrings and comments
- Test your tool thoroughly before deployment

#### Parameter Types
Supported parameter types:
- `"string"`: Text input
- `"integer"`: Whole numbers
- `"number"`: Decimal numbers
- `"boolean"`: True/false values
- `"array"`: Lists of values
- `"object"`: Complex objects

#### Error Handling
```python
def execute(self, **kwargs) -> Dict[str, Any]:
    try:
        # Tool logic here
        result = do_something()
        return {"content": result}
    except Exception as e:
        return {"content": f"Error in {self.name}: {str(e)}"}
```

## Tool Configuration

Tools can be enabled/disabled at runtime:

```python
from src.tools import get_tool_registry

registry = get_tool_registry()

# Enable a tool
registry.enable_tool("my_custom_tool")

# Disable a tool
registry.disable_tool("my_custom_tool")

# Check if tool is enabled
is_enabled = registry.is_tool_enabled("my_custom_tool")
```

## Examples

See the `examples/` directory for sample tool implementations that demonstrate various patterns and use cases.

## Testing Tools

Test your tools before deployment:

```python
from src.tools.custom.my_custom_tool import MyCustomTool

# Create tool instance
tool = MyCustomTool()

# Test execution
result = tool.execute(input_param="test value")
print(result)

# Test parameter validation
try:
    tool.execute()  # Missing required parameter
except ValueError as e:
    print(f"Validation error: {e}")
```