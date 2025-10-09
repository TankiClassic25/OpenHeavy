"""
Web search tool - custom tool for searching the web.
Migrated from the original agent.py web_search functionality.
Preserves the exact same API URL and behavior.
"""
import requests
from typing import Dict, Any, List, Optional
from src.tools.base import BaseTool
from src.models.tool import ToolParameter, ToolType
from config.settings import get_search_config


class WebSearchTool(BaseTool):
    """
    Custom tool for performing web searches using SearXNG.
    Preserves the original search functionality and API URL.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize the web search tool.
        
        Args:
            enabled: Whether the tool is enabled (default: True)
        """
        super().__init__(enabled=enabled)
        self._search_config = get_search_config()
    
    @property
    def name(self) -> str:
        """Tool name"""
        return "web_search"
    
    @property
    def description(self) -> str:
        """Tool description"""
        return "Perform a web search and return results."
    
    @property
    def tool_type(self) -> ToolType:
        """Tool type - custom user tool"""
        return ToolType.CUSTOM
    
    @property
    def version(self) -> str:
        """Tool version"""
        return "1.0.0"
    
    @property
    def author(self) -> str:
        """Tool author"""
        return "OpenHeavy"
    
    def get_parameters(self) -> List[ToolParameter]:
        """
        Get tool parameters.
        
        Returns:
            List of parameters this tool accepts
        """
        return [
            ToolParameter(
                name="query",
                type="string",
                description="Search query string",
                required=True
            ),
            ToolParameter(
                name="max_results",
                type="integer",
                description="Maximum number of results to return",
                required=False
            )
        ]
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute web search with the given parameters.
        Preserves the exact same logic and output format as the original.
        
        Args:
            **kwargs: Tool parameters (query, max_results)
            
        Returns:
            Dictionary with 'content' key containing formatted search results
        """
        # Validate parameters
        self.validate_parameters(kwargs)
        
        query = kwargs.get("query")
        max_results = kwargs.get("max_results")
        
        if max_results is None:
            max_results = self._search_config["max_results"]
        
        # Prepare search parameters - preserve original format
        params = {
            "q": query,
            "format": "json",
            "max_results": max_results
        }
        
        try:
            # Make request to search API - preserve original URL and timeout
            response = requests.get(
                self._search_config["url"], 
                params=params, 
                timeout=15
            )
            data = response.json()
            
            # Format results exactly as in the original implementation
            markdown = f"# Search Results: \"{data.get('query', query)}\"\n\n"
            markdown += f"**Total results:** {data.get('number_of_results', 'unknown')}\n\n---\n\n"

            for i, result in enumerate(data.get("results", []), start=1):
                markdown += f"### {i}. [{result.get('title', 'No title')}]({result.get('url', '#')})\n"
                markdown += f"{result.get('content', 'No description')}\n\n"
                markdown += f"**Source:** {result.get('engine', 'unknown')}\n\n---\n\n"
            
            return {"content": markdown}
            
        except Exception as e:
            # Return error in the same format as original
            return {"content": f"Error in web_search: {str(e)}"}
    
    def get_search_url(self) -> str:
        """Get the configured search URL"""
        return self._search_config["url"]
    
    def get_max_results(self) -> int:
        """Get the configured maximum results"""
        return self._search_config["max_results"]
    
    def test_connection(self) -> bool:
        """
        Test if the search service is available.
        
        Returns:
            True if search service responds, False otherwise
        """
        try:
            response = requests.get(
                self._search_config["url"],
                params={"q": "test", "format": "json", "max_results": 1},
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False