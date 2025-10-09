"""
WebSocket event handlers.
Handles all WebSocket events and delegates to appropriate services.
"""
import time
import threading
from flask_socketio import SocketIO, emit
from src.services.orchestrator import AgentOrchestrator
from src.models.events import IncomingMessageEvent
from src.utils.error_handlers import emit_error_to_client
import logging


logger = logging.getLogger(__name__)


def register_handlers(socketio: SocketIO, container) -> None:
    """
    Register all WebSocket event handlers.
    
    Args:
        socketio: SocketIO instance
        container: Dependency injection container
    """
    
    @socketio.on('connect')
    def handle_connect():
        """
        Handle client connection.
        Simple connection logging without authentication.
        """
        logger.info("Client connected")
    
    @socketio.on('disconnect')
    def handle_disconnect(data=None):
        """
        Handle client disconnection.
        Simple disconnection logging.
        
        Args:
            data: Optional data from client (usually None for disconnect)
        """
        logger.info("Client disconnected")
    
    @socketio.on('send_message')
    def handle_message(data):
        """
        Handle incoming user messages.
        Preserves the exact same logic as the original handle_message.
        
        Args:
            data: Message data from client
        """
        try:
            # Validate incoming data
            if not data or 'data' not in data:
                emit_error_to_client(
                    socketio, 
                    ValueError("Invalid message format")
                )
                return
            
            # Extract user message
            user_message = data['data']
            
            if not user_message or not user_message.strip():
                emit_error_to_client(
                    socketio, 
                    ValueError("Empty message")
                )
                return
            
            logger.info(f"Received message: {user_message[:100]}...")
            
            # Start agent workflow in background thread - preserve original behavior
            threading.Thread(
                target=start_agent_workflow, 
                args=(user_message, socketio, container)
            ).start()
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            emit_error_to_client(socketio, e)
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping requests for connection testing"""
        emit('pong', {'timestamp': time.time()})
    
    logger.info("WebSocket handlers registered")


def start_agent_workflow(user_message: str, socketio: SocketIO, container) -> None:
    """
    Start the agent workflow for processing user messages.
    Preserves the exact same logic as app.py start_agent_workflow().
    
    Args:
        user_message: User's message to process
        socketio: SocketIO instance for progress updates
        container: Dependency injection container
    """
    try:
        logger.info("Starting agent workflow")
        
        # Get orchestrator from container
        orchestrator = container.resolve(AgentOrchestrator)
        
        # Run complete workflow (agents + synthesis) - preserve original behavior
        final_answer = orchestrator.run_complete_workflow(
            user_request=user_message,
            socketio=socketio,
            streaming=True  # Enable streaming synthesis
        )
        
        logger.info("Agent workflow completed successfully")
        
    except Exception as e:
        logger.error(f"Agent workflow failed: {str(e)}")
        emit_error_to_client(socketio, e)


# Additional utility functions for WebSocket handling

def emit_agent_created(socketio: SocketIO, agent_id: str, total_steps: int) -> None:
    """
    Emit agent created event.
    
    Args:
        socketio: SocketIO instance
        agent_id: Agent identifier
        total_steps: Total number of steps in the plan
    """
    socketio.emit('agent_created', {
        'agent_id': agent_id,
        'total_steps': total_steps,
        'plan_ready': True
    })
    logger.debug(f"Emitted agent_created for {agent_id}")


def emit_agent_progress(socketio: SocketIO, agent_id: str, progress: int) -> None:
    """
    Emit agent progress update.
    
    Args:
        socketio: SocketIO instance
        agent_id: Agent identifier
        progress: Progress percentage (0-100)
    """
    socketio.emit('agent_progress', {
        'agent_id': agent_id, 
        'progress': progress
    })
    logger.debug(f"Emitted progress for {agent_id}: {progress}%")


def emit_timer_update(socketio: SocketIO, elapsed_time: int) -> None:
    """
    Emit timer update.
    
    Args:
        socketio: SocketIO instance
        elapsed_time: Elapsed time in seconds
    """
    socketio.emit('update_timer', {'time': elapsed_time})


def emit_agents_completed(socketio: SocketIO, total_agents: int, execution_time: float) -> None:
    """
    Emit agents completed event.
    Fixes the bug where progress bars were hardcoded to 4.
    
    Args:
        socketio: SocketIO instance
        total_agents: Actual number of agents that worked
        execution_time: Total execution time
    """
    socketio.emit('agents_completed', {
        'total_agents': total_agents,  # Use actual count instead of hardcoded 4
        'execution_time': execution_time
    })
    logger.info(f"Emitted agents_completed: {total_agents} agents, {execution_time:.2f}s")


def emit_final_answer_chunk(socketio: SocketIO, chunk: str) -> None:
    """
    Emit final answer chunk for streaming.
    
    Args:
        socketio: SocketIO instance
        chunk: Answer chunk
    """
    socketio.emit('final_answer_chunk', {'chunk': chunk})


def emit_final_answer_complete(socketio: SocketIO) -> None:
    """
    Emit final answer completion event.
    
    Args:
        socketio: SocketIO instance
    """
    socketio.emit('final_answer_complete')
    logger.info("Final answer streaming completed")


def validate_websocket_data(data: dict, required_fields: list) -> bool:
    """
    Validate WebSocket message data.
    
    Args:
        data: Data to validate
        required_fields: List of required field names
        
    Returns:
        True if data is valid
        
    Raises:
        ValueError: If data is invalid
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
        
        if not data[field]:
            raise ValueError(f"Field '{field}' cannot be empty")
    
    return True