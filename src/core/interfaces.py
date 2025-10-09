"""
Interfaces and protocols for the agent system.
Defines contracts for agent components to ensure consistency and testability.
"""
from abc import ABC, abstractmethod
from typing import Protocol, List, Dict, Any, Optional
from src.models.plan import Step, PlanResponse
from src.models.agent import AgentConfig, AgentState, AgentResult


class IPromptLoader(Protocol):
    """Protocol for loading system prompts from external sources"""
    
    def load_prompt(self, prompt_name: str) -> str:
        """
        Load a system prompt by name.
        
        Args:
            prompt_name: Name of the prompt to load
            
        Returns:
            Prompt content as string
            
        Raises:
            FileNotFoundError: If prompt file is not found
        """
        ...


class IPlanner(Protocol):
    """Protocol for creating execution plans from user requests"""
    
    def create_plan(self, user_request: str) -> PlanResponse:
        """
        Create an execution plan for the given user request.
        
        Args:
            user_request: User's request to plan for
            
        Returns:
            PlanResponse containing the execution steps
            
        Raises:
            PlanningError: If plan creation fails
        """
        ...


class IPlanExecutor(Protocol):
    """Protocol for executing individual steps in a plan"""
    
    def execute_step(self, step: Step, context: str) -> str:
        """
        Execute a single step in the plan.
        
        Args:
            step: Step to execute
            context: Execution context (previous results, user request)
            
        Returns:
            Step execution result as string
            
        Raises:
            ExecutionError: If step execution fails
        """
        ...


class IAnswerSynthesizer(Protocol):
    """Protocol for synthesizing answers from multiple agent results"""
    
    def synthesize_answer(
        self, 
        user_query: str, 
        agent_results: List[str]
    ) -> str:
        """
        Synthesize a final answer from multiple agent results.
        
        Args:
            user_query: Original user query
            agent_results: Results from multiple agents
            
        Returns:
            Synthesized final answer
            
        Raises:
            SynthesisError: If synthesis fails
        """
        ...


class ILLMService(Protocol):
    """Protocol for LLM service interactions"""
    
    def create_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Any:
        """
        Create a completion using the LLM service.
        
        Args:
            messages: Conversation messages
            tools: Available tools for the LLM
            **kwargs: Additional parameters
            
        Returns:
            LLM completion response
        """
        ...
    
    def create_structured_completion(
        self,
        messages: List[Dict[str, str]],
        response_format: type,
        **kwargs
    ) -> Any:
        """
        Create a structured completion with a specific response format.
        
        Args:
            messages: Conversation messages
            response_format: Pydantic model for response structure
            **kwargs: Additional parameters
            
        Returns:
            Structured LLM response
        """
        ...


class IAgentOrchestrator(Protocol):
    """Protocol for orchestrating multiple agents"""
    
    def run_agents(
        self,
        user_request: str,
        agent_configs: List[Dict[str, float]],
        socketio: Optional[Any] = None
    ) -> List[AgentResult]:
        """
        Run multiple agents concurrently.
        
        Args:
            user_request: User's request
            agent_configs: Configuration for each agent
            socketio: Optional SocketIO instance for progress updates
            
        Returns:
            List of agent results
        """
        ...


# Abstract base classes for concrete implementations

class BasePromptLoader(ABC):
    """Base class for prompt loaders"""
    
    @abstractmethod
    def load_prompt(self, prompt_name: str) -> str:
        """Load a system prompt by name"""
        pass


class BasePlanner(ABC):
    """Base class for plan creators"""
    
    def __init__(self, llm_service: ILLMService, prompt_loader: IPromptLoader):
        self.llm_service = llm_service
        self.prompt_loader = prompt_loader
    
    @abstractmethod
    def create_plan(self, user_request: str) -> PlanResponse:
        """Create an execution plan"""
        pass


class BasePlanExecutor(ABC):
    """Base class for plan executors"""
    
    def __init__(self, llm_service: ILLMService, agent_config: AgentConfig):
        self.llm_service = llm_service
        self.agent_config = agent_config
    
    @abstractmethod
    def execute_step(self, step: Step, context: str) -> str:
        """Execute a single step"""
        pass


class BaseAnswerSynthesizer(ABC):
    """Base class for answer synthesizers"""
    
    def __init__(self, llm_service: ILLMService, prompt_loader: IPromptLoader):
        self.llm_service = llm_service
        self.prompt_loader = prompt_loader
    
    @abstractmethod
    def synthesize_answer(self, user_query: str, agent_results: List[str]) -> str:
        """Synthesize final answer"""
        pass


class BaseAgent(ABC):
    """Base class for agents"""
    
    def __init__(
        self,
        agent_config: AgentConfig,
        planner: IPlanner,
        executor: IPlanExecutor
    ):
        self.config = agent_config
        self.planner = planner
        self.executor = executor
        self.state = AgentState(agent_id="")
    
    @abstractmethod
    def run(
        self,
        user_request: str,
        agent_id: str,
        socketio: Optional[Any] = None
    ) -> AgentResult:
        """Run the agent with the given request"""
        pass