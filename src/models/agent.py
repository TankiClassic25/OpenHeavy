"""
Agent-related Pydantic models.
Defines configuration and state models for agents.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"


class AgentConfig(BaseModel):
    """
    Configuration for an individual agent.
    Migrated from the original AgentConfig class.
    """
    base_url: str = Field(..., description="Base URL for the LLM API")
    api_key: str = Field(..., description="API key for authentication")
    model: str = Field(..., description="Model name to use")
    search_url: str = Field(..., description="URL for search API")
    max_search_results: int = Field(default=5, description="Maximum search results")
    max_retries: int = Field(default=3, description="Maximum retries per step")
    temperature: float = Field(default=0.3, description="Temperature for LLM")
    top_p: float = Field(default=0.9, description="Top-p for LLM")


class AgentState(BaseModel):
    """
    Current state of an agent during execution.
    Used for tracking progress and status.
    """
    agent_id: str = Field(..., description="Unique identifier for the agent")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="Current status")
    current_step: int = Field(default=0, description="Current step index")
    total_steps: int = Field(default=0, description="Total number of steps")
    progress: float = Field(default=0.0, description="Progress percentage (0-100)")
    error_message: Optional[str] = Field(None, description="Error message if status is ERROR")
    
    def update_progress(self) -> None:
        """Update progress percentage based on current and total steps"""
        if self.total_steps > 0:
            self.progress = round((self.current_step / self.total_steps) * 100, 2)
        else:
            self.progress = 0.0
    
    def advance_step(self) -> None:
        """Advance to the next step and update progress"""
        self.current_step += 1
        self.update_progress()
    
    def set_error(self, error_message: str) -> None:
        """Set agent to error state with message"""
        self.status = AgentStatus.ERROR
        self.error_message = error_message


class AgentResult(BaseModel):
    """
    Result from an agent's execution.
    Contains the final output and metadata.
    """
    agent_id: str = Field(..., description="Agent that produced this result")
    content: str = Field(..., description="Final result content")
    execution_time: float = Field(..., description="Execution time in seconds")
    steps_completed: int = Field(..., description="Number of steps completed")
    success: bool = Field(default=True, description="Whether execution was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MultiAgentResult(BaseModel):
    """
    Combined results from multiple agents.
    Used for synthesis and final response generation.
    """
    results: List[AgentResult] = Field(..., description="Results from individual agents")
    synthesized_content: Optional[str] = Field(None, description="Synthesized final answer")
    total_execution_time: float = Field(..., description="Total execution time")
    successful_agents: int = Field(..., description="Number of successful agents")
    
    def get_successful_results(self) -> List[AgentResult]:
        """Get only the successful agent results"""
        return [result for result in self.results if result.success]
    
    def get_failed_results(self) -> List[AgentResult]:
        """Get only the failed agent results"""
        return [result for result in self.results if not result.success]