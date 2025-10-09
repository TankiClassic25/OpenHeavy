"""
Main Agent class - refactored to use modular components.
Maintains the same public interface while using the new architecture.
"""
import time
from typing import Optional, Any, List
from src.core.interfaces import BaseAgent, IPlanner, IPlanExecutor, ILLMService
from src.models.agent import AgentConfig, AgentState, AgentResult, AgentStatus
from src.models.plan import PlanResponse
from src.exceptions.agent import AgentError, AgentTimeoutError
from src.core.planner import TaskPlanner
from src.core.executor import PlanExecutor
from src.core.prompt_loader import get_prompt_loader
import logging


logger = logging.getLogger(__name__)


class Agent(BaseAgent):
    """
    Main agent class that coordinates planning and execution.
    Refactored to use modular components while preserving the original interface.
    """
    
    def __init__(
        self,
        agent_config: AgentConfig,
        llm_service: ILLMService,
        planner: Optional[IPlanner] = None,
        executor: Optional[IPlanExecutor] = None
    ):
        """
        Initialize the agent with configuration and components.
        
        Args:
            agent_config: Agent configuration
            llm_service: LLM service for API calls
            planner: Optional custom planner (will create default if None)
            executor: Optional custom executor (will create default if None)
        """
        # Create default components if not provided
        prompt_loader = get_prompt_loader()
        
        if planner is None:
            planner = TaskPlanner(llm_service, prompt_loader)
        
        if executor is None:
            executor = PlanExecutor(llm_service, agent_config)
        
        super().__init__(agent_config, planner, executor)
        
        self.llm_service = llm_service
        self._current_plan: Optional[PlanResponse] = None
        self._execution_start_time: Optional[float] = None
    
    def run(
        self,
        user_request: str,
        agent_id: str,
        socketio: Optional[Any] = None,
        first_agent_plan_ready: Optional[Any] = None
    ) -> AgentResult:
        """
        Run the agent with the given request.
        Maintains the same interface as the original run_agent function.
        
        Args:
            user_request: User's request to process
            agent_id: Unique identifier for this agent
            socketio: Optional SocketIO instance for progress updates
            first_agent_plan_ready: Optional threading event for timer coordination
            
        Returns:
            AgentResult with the execution result
        """
        self.state.agent_id = agent_id
        self.state.status = AgentStatus.PLANNING
        self._execution_start_time = time.time()
        
        try:
            logger.info(f"Agent {agent_id} starting execution")
            
            # Create execution plan
            self.state.status = AgentStatus.PLANNING
            plan = self.create_plan(user_request)
            self._current_plan = plan
            
            # Signal that plan is ready (for timer start) - but don't wait for others
            if first_agent_plan_ready and not first_agent_plan_ready.is_set():
                first_agent_plan_ready.set()
            
            # Update state with plan information
            self.state.total_steps = len(plan.plan)
            self.state.update_progress()
            
            # Execute the plan immediately - don't wait for other agents
            self.state.status = AgentStatus.EXECUTING
            result_content = self.run_plan(
                plan, 
                user_request, 
                socketio, 
                agent_id
            )
            
            # Mark as completed
            self.state.status = AgentStatus.COMPLETED
            execution_time = time.time() - self._execution_start_time
            
            logger.info(f"Agent {agent_id} completed successfully in {execution_time:.2f}s")
            
            return AgentResult(
                agent_id=agent_id,
                content=result_content,
                execution_time=execution_time,
                steps_completed=self.state.current_step,
                success=True,
                metadata={
                    "total_steps": self.state.total_steps,
                    "temperature": self.config.temperature,
                    "top_p": self.config.top_p
                }
            )
            
        except Exception as e:
            self.state.set_error(str(e))
            execution_time = time.time() - self._execution_start_time if self._execution_start_time else 0
            
            logger.error(f"Agent {agent_id} failed: {str(e)}")
            
            return AgentResult(
                agent_id=agent_id,
                content="",
                execution_time=execution_time,
                steps_completed=self.state.current_step,
                success=False,
                error_message=str(e),
                metadata={
                    "error_type": e.__class__.__name__,
                    "total_steps": self.state.total_steps,
                    "temperature": self.config.temperature,
                    "top_p": self.config.top_p
                }
            )
    
    def create_plan(self, user_request: str) -> PlanResponse:
        """
        Create an execution plan for the user request.
        Delegates to the planner component.
        
        Args:
            user_request: User's request
            
        Returns:
            Execution plan
        """
        try:
            return self.planner.create_plan(user_request)
        except Exception as e:
            raise AgentError(
                f"Failed to create plan: {str(e)}",
                agent_id=self.state.agent_id,
                cause=e
            )
    
    def run_plan(
        self,
        plan: PlanResponse,
        user_task: str,
        socketio: Optional[Any] = None,
        agent_id: Optional[str] = None
    ) -> str:
        """
        Execute the plan step by step.
        Preserves the exact same logic as Agent.run_plan().
        
        Args:
            plan: Plan to execute
            user_task: Original user task
            socketio: Optional SocketIO for progress updates
            agent_id: Agent identifier
            
        Returns:
            Final result from the plan execution
        """
        history = []
        
        for idx, step in enumerate(plan.plan):
            # Emit agent_created event on first step - each agent works independently
            if socketio and agent_id and idx == 0:
                socketio.emit('agent_created', {
                    'agent_id': agent_id,
                    'total_steps': len(plan.plan),
                    'plan_ready': True
                })
            
            # Build context for this step
            user_msg = self._build_step_context(plan, idx, history, user_task)
            
            # Execute the step
            step_output = self.executor.execute_step(step, user_msg)
            history.append(step_output)
            
            # Update progress
            self.state.advance_step()
            
            # Emit progress update - preserve original behavior
            if socketio and agent_id:
                progress = round(((idx + 1) / len(plan.plan)) * 100)
                socketio.emit('agent_progress', {'agent_id': agent_id, 'progress': progress})
            
            # If this is the report step, return the result
            if step.report:
                return step_output
        
        # Return the last result if no report step was found
        return history[-1] if history else ""
    
    def _build_step_context(
        self, 
        plan: PlanResponse, 
        idx: int, 
        history: List[str], 
        user_task: str
    ) -> str:
        """
        Build context for step execution.
        Preserves the exact same logic as the original implementation.
        
        Args:
            plan: Execution plan
            idx: Current step index
            history: Previous step results
            user_task: Original user task
            
        Returns:
            Context string for step execution
        """
        prev_context = "\n".join([
            f"Step {i + 1} ({step.title}) result:\n{result}" 
            for i, (step, result) in enumerate(zip(plan.plan[:idx], history))
        ])
        
        user_msg = f"User task: {user_task}"
        if prev_context:
            user_msg += f"\n\nPrevious context:\n{prev_context}"
        
        return user_msg
    
    def get_current_state(self) -> AgentState:
        """
        Get the current state of the agent.
        
        Returns:
            Current agent state
        """
        return self.state
    
    def get_current_plan(self) -> Optional[PlanResponse]:
        """
        Get the current execution plan.
        
        Returns:
            Current plan if available
        """
        return self._current_plan
    
    def get_execution_time(self) -> float:
        """
        Get the current execution time.
        
        Returns:
            Execution time in seconds
        """
        if self._execution_start_time is None:
            return 0.0
        return time.time() - self._execution_start_time


# Factory function to maintain compatibility with original interface
def run_agent(
    user_task: str, 
    socketio: Optional[Any] = None, 
    agent_id: Optional[str] = None, 
    first_agent_plan_ready: Optional[Any] = None,
    temperature: float = 0.3, 
    top_p: float = 0.9
) -> str:
    """
    Factory function that maintains compatibility with the original run_agent function.
    Creates an agent and runs it with the specified parameters.
    
    Args:
        user_task: User's task to execute
        socketio: Optional SocketIO instance
        agent_id: Optional agent identifier
        first_agent_plan_ready: Optional threading event for timer coordination
        temperature: LLM temperature setting
        top_p: LLM top_p setting
        
    Returns:
        Agent execution result as string
    """
    from config.settings import get_llm_config
    from src.services.llm_service import LLMService
    
    # Create agent configuration
    llm_config = get_llm_config()
    agent_config = AgentConfig(
        base_url=llm_config["base_url"],
        api_key=llm_config["api_key"],
        model=llm_config["model"],
        search_url="",  # Not used directly by agent
        max_search_results=5,  # Not used directly by agent
        max_retries=llm_config["max_retries"],
        temperature=temperature,
        top_p=top_p
    )
    
    # Create LLM service
    llm_service = LLMService(agent_config)
    
    # Create and run agent
    agent = Agent(agent_config, llm_service)
    result = agent.run(
        user_task, 
        agent_id or "default_agent", 
        socketio,
        first_agent_plan_ready
    )
    
    return result.content