"""
WebSocket event models.
Defines all events that can be sent between client and server.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base class for all WebSocket events"""
    event_type: str = Field(..., description="Type of the event")
    timestamp: Optional[float] = Field(None, description="Event timestamp")


class IncomingMessageEvent(BaseModel):
    """Event for incoming user messages"""
    data: str = Field(..., description="User message content")


class AgentCreatedEvent(BaseEvent):
    """Event sent when an agent is created and starts working"""
    event_type: str = Field(default="agent_created", description="Event type")
    agent_id: str = Field(..., description="Unique identifier for the agent")
    total_steps: int = Field(..., description="Total number of steps in the plan")
    plan_ready: bool = Field(default=True, description="Whether the plan is ready")


class AgentProgressEvent(BaseEvent):
    """Event sent to update agent progress"""
    event_type: str = Field(default="agent_progress", description="Event type")
    agent_id: str = Field(..., description="Agent identifier")
    progress: int = Field(..., description="Progress percentage (0-100)")


class TimerUpdateEvent(BaseEvent):
    """Event sent to update the global timer"""
    event_type: str = Field(default="update_timer", description="Event type")
    time: int = Field(..., description="Elapsed time in seconds")


class AgentsCompletedEvent(BaseEvent):
    """Event sent when all agents have completed their work"""
    event_type: str = Field(default="agents_completed", description="Event type")
    total_agents: int = Field(..., description="Total number of agents that worked")
    execution_time: float = Field(..., description="Total execution time")


class FinalAnswerChunkEvent(BaseEvent):
    """Event sent for streaming the final synthesized answer"""
    event_type: str = Field(default="final_answer_chunk", description="Event type")
    chunk: str = Field(..., description="Chunk of the final answer")


class FinalAnswerCompleteEvent(BaseEvent):
    """Event sent when the final answer streaming is complete"""
    event_type: str = Field(default="final_answer_complete", description="Event type")


class ErrorEvent(BaseEvent):
    """Event sent when an error occurs"""
    event_type: str = Field(default="error", description="Event type")
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ConnectionEvent(BaseEvent):
    """Event for connection status changes"""
    event_type: str = Field(default="connection", description="Event type")
    status: str = Field(..., description="Connection status: connected, disconnected")
    client_id: Optional[str] = Field(None, description="Client identifier")


# Event type mapping for easy access
EVENT_TYPES = {
    "agent_created": AgentCreatedEvent,
    "agent_progress": AgentProgressEvent,
    "update_timer": TimerUpdateEvent,
    "agents_completed": AgentsCompletedEvent,
    "final_answer_chunk": FinalAnswerChunkEvent,
    "final_answer_complete": FinalAnswerCompleteEvent,
    "error": ErrorEvent,
    "connection": ConnectionEvent,
}