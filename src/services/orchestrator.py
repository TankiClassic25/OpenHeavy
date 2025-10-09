"""
Multi-agent orchestrator for coordinating multiple agents.
Extracts orchestration logic from app.py while preserving behavior.
"""
import time
import threading
from typing import List, Dict, Any, Optional, Callable

from src.core.interfaces import IAgentOrchestrator, ILLMService, IAnswerSynthesizer
from src.models.agent import AgentResult, MultiAgentResult, AgentConfig
from src.core.agent import Agent
from src.core.synthesizer import AnswerSynthesizer
from src.core.prompt_loader import get_prompt_loader
from src.services.llm_service import LLMService
from src.exceptions.agent import AgentError, SynthesisError
from config.settings import get_agent_configs, get_llm_config
import logging


logger = logging.getLogger(__name__)


class AgentOrchestrator(IAgentOrchestrator):
    """
    Orchestrates multiple agents running concurrently.
    Preserves the exact same coordination logic as app.py.
    """
    
    def __init__(
        self,
        llm_service: Optional[ILLMService] = None,
        synthesizer: Optional[IAnswerSynthesizer] = None
    ):
        """
        Initialize the agent orchestrator.
        
        Args:
            llm_service: Optional LLM service (will create default if None)
            synthesizer: Optional synthesizer (will create default if None)
        """
        # Create default LLM service if not provided
        if llm_service is None:
            llm_config = get_llm_config()
            default_config = AgentConfig(
                base_url=llm_config["base_url"],
                api_key=llm_config["api_key"],
                model=llm_config["model"],
                search_url="",  # Not used by orchestrator
                max_search_results=5,
                max_retries=llm_config["max_retries"],
                temperature=0.3,  # Default for orchestrator
                top_p=0.9
            )
            llm_service = LLMService(default_config)
        
        self.llm_service = llm_service
        
        # Create default synthesizer if not provided
        if synthesizer is None:
            prompt_loader = get_prompt_loader()
            synthesizer = AnswerSynthesizer(llm_service, prompt_loader)
        
        self.synthesizer = synthesizer
        self.agent_results: Dict[str, AgentResult] = {}
    
    def run_agents(
        self,
        user_request: str,
        agent_configs: Optional[List[Dict[str, float]]] = None,
        socketio: Optional[Any] = None,
        progress_callback: Optional[Callable] = None
    ) -> MultiAgentResult:
        """
        Run multiple agents concurrently.
        Preserves the exact same logic as app.py start_agent_workflow().
        
        Args:
            user_request: User's request
            agent_configs: Configuration for each agent (uses default if None)
            socketio: Optional SocketIO instance for progress updates
            progress_callback: Optional callback for progress updates
            
        Returns:
            MultiAgentResult with all agent results and synthesis
        """
        execution_start_time = time.time()
        
        # Use default agent configs if not provided
        if agent_configs is None:
            agent_configs = get_agent_configs()
        
        logger.info(f"Starting orchestration with {len(agent_configs)} agents")
        
        # Clear previous results
        self.agent_results = {}
        
        # Create threading event for timer coordination - wait for first plan
        first_agent_plan_ready = threading.Event()
        threads = []
        
        # Start all agents concurrently - each agent works independently
        for i, config in enumerate(agent_configs):
            agent_id = f'agent_{i+1}'
            thread = threading.Thread(
                target=self._run_agent_wrapper,
                args=(
                    user_request, 
                    agent_id, 
                    config["temperature"], 
                    config["top_p"],
                    socketio,
                    first_agent_plan_ready
                )
            )
            threads.append(thread)
            thread.start()
        
        # Wait for first agent to create plan (not complete execution) - for timer start
        first_agent_plan_ready.wait()
        
        # Start timer from this moment - after first plan is ready
        timer_start_time = time.time()
        timer_thread = None
        timer_stop_event = threading.Event()
        
        if socketio:
            # Use SocketIO background task like in original
            timer_thread = socketio.start_background_task(
                target=self._update_global_timer_socketio,
                socketio_instance=socketio,
                start_time=timer_start_time,
                stop_event=timer_stop_event
            )
        elif progress_callback:
            # Fallback to regular thread for non-socketio usage
            timer_thread = threading.Thread(
                target=self._update_global_timer,
                args=(timer_start_time, progress_callback, timer_stop_event)
            )
            timer_thread.start()
        
        # Wait for all agents to complete
        for thread in threads:
            thread.join()
        
        # Stop timer
        if timer_thread:
            timer_stop_event.set()
            # For SocketIO background tasks, we don't need to join
            if not socketio:
                timer_thread.join()
        
        total_execution_time = time.time() - execution_start_time
        
        # Emit agents completed event if socketio provided
        if socketio:
            event_data = {
                'total_agents': len(agent_configs),
                'execution_time': total_execution_time
            }
            socketio.emit('agents_completed', event_data)
        
        # Collect results
        results = list(self.agent_results.values())
        successful_results = [r for r in results if r.success]
        
        logger.info(
            f"Orchestration completed: {len(successful_results)}/{len(results)} agents successful"
        )
        
        return MultiAgentResult(
            results=results,
            total_execution_time=total_execution_time,
            successful_agents=len(successful_results)
        )
    
    def synthesize_final_answer(
        self,
        user_query: str,
        multi_agent_result: MultiAgentResult,
        socketio: Optional[Any] = None,
        streaming: bool = True
    ) -> str:
        """
        Synthesize final answer from agent results.
        
        Args:
            user_query: Original user query
            multi_agent_result: Results from multiple agents
            socketio: Optional SocketIO for streaming
            streaming: Whether to use streaming synthesis
            
        Returns:
            Synthesized final answer
        """
        try:
            # Get successful results only
            successful_results = multi_agent_result.get_successful_results()
            
            if not successful_results:
                raise SynthesisError(
                    "No successful agent results to synthesize",
                    agent_count=len(multi_agent_result.results),
                    successful_agents=0
                )
            
            # Extract content from results
            agent_contents = [result.content for result in successful_results]
            
            logger.info(f"Synthesizing answer from {len(agent_contents)} successful agents")
            
            if streaming and socketio:
                # Use streaming synthesis
                synthesized_content = ""
                
                def emit_chunk(chunk):
                    socketio.emit('final_answer_chunk', {'chunk': chunk})
                
                for chunk in self.synthesizer.synthesize_answer_streaming(
                    user_query, 
                    agent_contents,
                    chunk_callback=emit_chunk
                ):
                    synthesized_content += chunk
                
                # Emit completion event
                socketio.emit('final_answer_complete')
                
                return synthesized_content
            else:
                # Use non-streaming synthesis
                return self.synthesizer.synthesize_answer(user_query, agent_contents)
                
        except Exception as e:
            logger.error(f"Final answer synthesis failed: {str(e)}")
            raise SynthesisError(
                f"Failed to synthesize final answer: {str(e)}",
                agent_count=len(multi_agent_result.results),
                successful_agents=len(multi_agent_result.get_successful_results()),
                cause=e
            )
    
    def run_complete_workflow(
        self,
        user_request: str,
        agent_configs: Optional[List[Dict[str, float]]] = None,
        socketio: Optional[Any] = None,
        streaming: bool = True
    ) -> str:
        """
        Run the complete workflow: agents + synthesis.
        Combines agent execution and answer synthesis.
        
        Args:
            user_request: User's request
            agent_configs: Agent configurations
            socketio: Optional SocketIO instance
            streaming: Whether to use streaming synthesis
            
        Returns:
            Final synthesized answer
        """
        # Run agents
        multi_result = self.run_agents(
            user_request, 
            agent_configs, 
            socketio,
            progress_callback=lambda elapsed: self._emit_timer_update(socketio, elapsed) if socketio else None
        )
        
        # Synthesize answer
        final_answer = self.synthesize_final_answer(
            user_request,
            multi_result,
            socketio,
            streaming
        )
        
        # Update multi_result with synthesized content
        multi_result.synthesized_content = final_answer
        
        return final_answer
    
    def _run_agent_wrapper(
        self,
        user_request: str,
        agent_id: str,
        temperature: float,
        top_p: float,
        socketio: Optional[Any] = None,
        first_agent_plan_ready: Optional[threading.Event] = None
    ) -> None:
        """
        Wrapper for running a single agent.
        Preserves the exact same logic as app.py run_agent_wrapper().
        
        Args:
            user_request: User's request
            agent_id: Agent identifier
            temperature: Temperature setting
            top_p: Top-p setting
            socketio: Optional SocketIO instance
            first_agent_plan_ready: Threading event for coordination
        """
        try:
            # Create agent configuration
            llm_config = get_llm_config()
            agent_config = AgentConfig(
                base_url=llm_config["base_url"],
                api_key=llm_config["api_key"],
                model=llm_config["model"],
                search_url="",  # Not used directly by agent
                max_search_results=5,
                max_retries=llm_config["max_retries"],
                temperature=temperature,
                top_p=top_p
            )
            
            # Create LLM service for this agent
            llm_service = LLMService(agent_config)
            
            # Create and run agent
            agent = Agent(agent_config, llm_service)
            result = agent.run(
                user_request,
                agent_id,
                socketio,
                first_agent_plan_ready
            )
            
            # Store result
            self.agent_results[agent_id] = result
            
            logger.info(f"Agent {agent_id} completed: success={result.success}")
            
            # Emit completion event if socketio provided
            if socketio:
                socketio.emit('agent_completed', {
                    'agent_id': agent_id,
                    'success': result.success,
                    'execution_time': result.execution_time
                })
            
        except Exception as e:
            logger.error(f"Agent {agent_id} failed: {str(e)}")
            
            # Emit failure event if socketio provided
            if socketio:
                socketio.emit('agent_failed', {
                    'agent_id': agent_id,
                    'error': str(e)
                })
            
            # Create failed result
            failed_result = AgentResult(
                agent_id=agent_id,
                content="",
                execution_time=0.0,
                steps_completed=0,
                success=False,
                error_message=str(e)
            )
            
            self.agent_results[agent_id] = failed_result
    
    def _update_global_timer(
        self,
        start_time: float,
        progress_callback: Callable,
        stop_event: threading.Event
    ) -> None:
        """
        Update global timer for progress tracking.
        Preserves the exact same logic as app.py update_global_timer().
        
        Args:
            start_time: Start time of execution
            progress_callback: Callback for timer updates
            stop_event: Event to stop the timer
        """
        while not stop_event.is_set():
            elapsed_time = int(time.time() - start_time)
            progress_callback(elapsed_time)
            time.sleep(1)
    
    def _update_global_timer_socketio(
        self,
        socketio_instance,
        start_time: float,
        stop_event: threading.Event
    ) -> None:
        """
        Update global timer for SocketIO - preserves original behavior.
        
        Args:
            socketio_instance: SocketIO instance to emit events
            start_time: Start time of execution
            stop_event: Event to stop the timer
        """
        while not stop_event.is_set():
            elapsed_time = int(time.time() - start_time)
            socketio_instance.emit('update_timer', {'time': elapsed_time})
            socketio_instance.sleep(1)  # Use socketio.sleep instead of time.sleep
    
    def get_orchestration_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the orchestration results.
        
        Returns:
            Dictionary with orchestration summary
        """
        if not self.agent_results:
            return {"status": "no_results"}
        
        successful_agents = [r for r in self.agent_results.values() if r.success]
        failed_agents = [r for r in self.agent_results.values() if not r.success]
        
        return {
            "total_agents": len(self.agent_results),
            "successful_agents": len(successful_agents),
            "failed_agents": len(failed_agents),
            "success_rate": len(successful_agents) / len(self.agent_results) * 100,
            "average_execution_time": sum(r.execution_time for r in successful_agents) / len(successful_agents) if successful_agents else 0,
            "agent_details": {
                agent_id: {
                    "success": result.success,
                    "execution_time": result.execution_time,
                    "steps_completed": result.steps_completed,
                    "error": result.error_message
                }
                for agent_id, result in self.agent_results.items()
            }
        }
    
    def _emit_timer_update(self, socketio: Any, elapsed: int) -> None:
        """Helper method to emit timer updates"""
        socketio.emit('update_timer', {'time': elapsed})