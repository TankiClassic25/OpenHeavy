"""
WebSocket event emitters.
Centralized functions for emitting WebSocket events to clients.
Fixes the progress bar bug and provides consistent event emission.
"""
import time
from typing import Optional, Dict, Any, List
from flask_socketio import SocketIO
from src.models.events import (
    AgentCreatedEvent, AgentProgressEvent, TimerUpdateEvent,
    AgentsCompletedEvent, FinalAnswerChunkEvent, FinalAnswerCompleteEvent,
    ErrorEvent
)
import logging


logger = logging.getLogger(__name__)


class WebSocketEmitter:
    """
    Centralized WebSocket event emitter.
    Provides consistent event emission with proper error handling.
    """
    
    def __init__(self, socketio: SocketIO):
        """
        Initialize the emitter.
        
        Args:
            socketio: SocketIO instance
        """
        self.socketio = socketio
    
    def emit_agent_created(
        self, 
        agent_id: str, 
        total_steps: int
    ) -> None:
        """
        Emit agent created event.
        
        Args:
            agent_id: Agent identifier
            total_steps: Total number of steps in the plan
        """
        event = AgentCreatedEvent(
            agent_id=agent_id,
            total_steps=total_steps,
            plan_ready=True
        )
        
        self._emit_event('agent_created', event.dict(exclude={'event_type'}))
        logger.debug(f"Emitted agent_created for {agent_id} with {total_steps} steps")
    
    def emit_agent_progress(
        self, 
        agent_id: str, 
        progress: int
    ) -> None:
        """
        Emit agent progress update.
        
        Args:
            agent_id: Agent identifier
            progress: Progress percentage (0-100)
        """
        event = AgentProgressEvent(
            agent_id=agent_id,
            progress=progress
        )
        
        self._emit_event('agent_progress', event.dict(exclude={'event_type'}))
        logger.debug(f"Emitted progress for {agent_id}: {progress}%")
    
    def emit_timer_update(
        self, 
        elapsed_time: int
    ) -> None:
        """
        Emit timer update.
        
        Args:
            elapsed_time: Elapsed time in seconds
        """
        event = TimerUpdateEvent(time=elapsed_time)
        
        self._emit_event('update_timer', event.dict(exclude={'event_type'}))
    
    def emit_agents_completed(
        self, 
        total_agents: int, 
        execution_time: float
    ) -> None:
        """
        Emit agents completed event.
        FIXES BUG: Uses actual number of agents instead of hardcoded 4.
        
        Args:
            total_agents: Actual number of agents that worked
            execution_time: Total execution time
        """
        event = AgentsCompletedEvent(
            total_agents=total_agents,
            execution_time=execution_time
        )
        
        self._emit_event('agents_completed', event.dict(exclude={'event_type'}))
        logger.info(f"Emitted agents_completed: {total_agents} agents, {execution_time:.2f}s")
    
    def emit_final_answer_chunk(
        self, 
        chunk: str
    ) -> None:
        """
        Emit final answer chunk for streaming.
        
        Args:
            chunk: Answer chunk
        """
        event = FinalAnswerChunkEvent(chunk=chunk)
        
        self._emit_event('final_answer_chunk', event.dict(exclude={'event_type'}))
    
    def emit_final_answer_complete(self) -> None:
        """
        Emit final answer completion event.
        """
        event = FinalAnswerCompleteEvent()
        
        self._emit_event('final_answer_complete', event.dict(exclude={'event_type'}))
        logger.info("Final answer streaming completed")
    
    def emit_error(
        self, 
        error_code: str, 
        error_message: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Emit error event.
        
        Args:
            error_code: Error code
            error_message: Human-readable error message
            details: Optional error details
        """
        event = ErrorEvent(
            error_code=error_code,
            error_message=error_message,
            details=details
        )
        
        self._emit_event('error', event.dict(exclude={'event_type'}))
        logger.warning(f"Emitted error: {error_code} - {error_message}")
    
    def emit_custom_event(
        self, 
        event_name: str, 
        data: Dict[str, Any]
    ) -> None:
        """
        Emit custom event.
        
        Args:
            event_name: Name of the event
            data: Event data
        """
        self._emit_event(event_name, data)
        logger.debug(f"Emitted custom event: {event_name}")
    
    def _emit_event(
        self, 
        event_name: str, 
        data: Dict[str, Any]
    ) -> None:
        """
        Internal method to emit events with error handling.
        
        Args:
            event_name: Name of the event
            data: Event data
        """
        try:
            self.socketio.emit(event_name, data)
        except Exception as e:
            logger.error(f"Failed to emit event {event_name}: {str(e)}")


# Utility functions for backward compatibility and convenience

def create_emitter(socketio: SocketIO) -> WebSocketEmitter:
    """
    Create a WebSocket emitter instance.
    
    Args:
        socketio: SocketIO instance
        
    Returns:
        WebSocketEmitter instance
    """
    return WebSocketEmitter(socketio)


def emit_agent_workflow_events(
    socketio: SocketIO,
    agent_results: List[Dict[str, Any]],
    total_execution_time: float
) -> None:
    """
    Emit a complete set of agent workflow events.
    Useful for testing or batch event emission.
    
    Args:
        socketio: SocketIO instance
        agent_results: List of agent result dictionaries
        total_execution_time: Total execution time
    """
    emitter = WebSocketEmitter(socketio)
    
    # Emit agents completed with correct count
    emitter.emit_agents_completed(
        total_agents=len(agent_results),
        execution_time=total_execution_time
    )


def emit_streaming_synthesis(
    socketio: SocketIO,
    content_chunks: List[str],
    chunk_delay: float = 0.05
) -> None:
    """
    Emit streaming synthesis chunks.
    
    Args:
        socketio: SocketIO instance
        content_chunks: List of content chunks
        chunk_delay: Delay between chunks in seconds
    """
    emitter = WebSocketEmitter(socketio)
    
    for chunk in content_chunks:
        emitter.emit_final_answer_chunk(chunk)
        if chunk_delay > 0:
            time.sleep(chunk_delay)
    
    emitter.emit_final_answer_complete()


def emit_agent_progress_sequence(
    socketio: SocketIO,
    agent_id: str,
    total_steps: int,
    step_delay: float = 1.0
) -> None:
    """
    Emit a sequence of progress updates for an agent.
    Useful for testing or simulation.
    
    Args:
        socketio: SocketIO instance
        agent_id: Agent identifier
        total_steps: Total number of steps
        step_delay: Delay between progress updates
    """
    emitter = WebSocketEmitter(socketio)
    
    # Emit agent created
    emitter.emit_agent_created(agent_id, total_steps)
    
    # Emit progress updates
    for step in range(1, total_steps + 1):
        progress = round((step / total_steps) * 100)
        emitter.emit_agent_progress(agent_id, progress)
        
        if step < total_steps and step_delay > 0:
            time.sleep(step_delay)


def emit_error_from_exception(
    socketio: SocketIO,
    exception: Exception
) -> None:
    """
    Emit error event from an exception.
    
    Args:
        socketio: SocketIO instance
        exception: Exception to emit
    """
    emitter = WebSocketEmitter(socketio)
    
    # Determine error code and message
    error_code = exception.__class__.__name__.upper()
    error_message = str(exception)
    
    # Add details if it's a custom exception
    details = None
    if hasattr(exception, 'details'):
        details = exception.details
    
    emitter.emit_error(error_code, error_message, details)