"""
Dependency Injection container for OpenHeavy application.
Manages service registration, resolution, and lifecycle.
"""
from typing import Dict, Any, Type, Callable, Optional, TypeVar, Generic, List
from abc import ABC, abstractmethod
import logging


logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime:
    """Service lifetime constants"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"


class ServiceDescriptor:
    """Describes how a service should be created and managed"""
    
    def __init__(
        self,
        service_type: Type,
        implementation: Optional[Type] = None,
        factory: Optional[Callable] = None,
        instance: Optional[Any] = None,
        lifetime: str = ServiceLifetime.TRANSIENT
    ):
        self.service_type = service_type
        self.implementation = implementation
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime
        
        # Validation
        if sum(bool(x) for x in [implementation, factory, instance]) != 1:
            raise ValueError("Exactly one of implementation, factory, or instance must be provided")


class Container:
    """
    Dependency injection container for managing services.
    Supports singleton and transient lifetimes.
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._building: set = set()  # Prevent circular dependencies
    
    def register_singleton(
        self, 
        service_type: Type[T], 
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        instance: Optional[T] = None
    ) -> 'Container':
        """
        Register a singleton service.
        
        Args:
            service_type: Service interface or type
            implementation: Implementation class
            factory: Factory function
            instance: Pre-created instance
            
        Returns:
            Self for method chaining
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        self._services[service_type] = descriptor
        logger.debug(f"Registered singleton service: {service_type.__name__}")
        return self
    
    def register_transient(
        self, 
        service_type: Type[T], 
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'Container':
        """
        Register a transient service (new instance each time).
        
        Args:
            service_type: Service interface or type
            implementation: Implementation class
            factory: Factory function
            
        Returns:
            Self for method chaining
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT
        )
        
        self._services[service_type] = descriptor
        logger.debug(f"Registered transient service: {service_type.__name__}")
        return self
    

    
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance.
        
        Args:
            service_type: Type of service to resolve
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service is not registered or circular dependency detected
        """
        if service_type not in self._services:
            raise ValueError(f"Service {service_type.__name__} is not registered")
        
        if service_type in self._building:
            raise ValueError(f"Circular dependency detected for {service_type.__name__}")
        
        descriptor = self._services[service_type]
        
        # Handle different lifetimes
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            return self._resolve_singleton(service_type, descriptor)
        else:  # TRANSIENT
            return self._resolve_transient(service_type, descriptor)
    
    def _resolve_singleton(self, service_type: Type[T], descriptor: ServiceDescriptor) -> T:
        """Resolve singleton service"""
        if service_type in self._singletons:
            return self._singletons[service_type]
        
        instance = self._create_instance(service_type, descriptor)
        self._singletons[service_type] = instance
        return instance
    

    
    def _resolve_transient(self, service_type: Type[T], descriptor: ServiceDescriptor) -> T:
        """Resolve transient service"""
        return self._create_instance(service_type, descriptor)
    
    def _create_instance(self, service_type: Type[T], descriptor: ServiceDescriptor) -> T:
        """Create service instance based on descriptor"""
        self._building.add(service_type)
        
        try:
            if descriptor.instance is not None:
                return descriptor.instance
            
            if descriptor.factory is not None:
                return descriptor.factory()
            
            if descriptor.implementation is not None:
                return self._create_with_dependencies(descriptor.implementation)
            
            # Fallback to service_type itself
            return self._create_with_dependencies(service_type)
            
        finally:
            self._building.discard(service_type)
    
    def _create_with_dependencies(self, implementation_type: Type[T]) -> T:
        """Create instance with dependency injection"""
        try:
            # Get constructor parameters
            import inspect
            signature = inspect.signature(implementation_type.__init__)
            parameters = list(signature.parameters.values())[1:]  # Skip 'self'
            
            # Resolve dependencies
            kwargs = {}
            for param in parameters:
                if param.annotation != inspect.Parameter.empty:
                    # Try to resolve the parameter type
                    try:
                        kwargs[param.name] = self.resolve(param.annotation)
                    except ValueError:
                        # If dependency not registered, check if parameter has default
                        if param.default == inspect.Parameter.empty:
                            logger.warning(
                                f"Cannot resolve dependency {param.annotation.__name__} "
                                f"for {implementation_type.__name__}"
                            )
                        # Continue without this dependency
            
            return implementation_type(**kwargs)
            
        except Exception as e:
            logger.error(f"Failed to create instance of {implementation_type.__name__}: {str(e)}")
            raise ValueError(f"Cannot create instance of {implementation_type.__name__}: {str(e)}")
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered"""
        return service_type in self._services
    
    def get_registered_services(self) -> Dict[Type, ServiceDescriptor]:
        """Get all registered services"""
        return self._services.copy()



# Global container instance
_global_container: Optional[Container] = None


def get_container() -> Container:
    """
    Get the global container instance.
    
    Returns:
        Global Container instance
    """
    global _global_container
    if _global_container is None:
        _global_container = Container()
    return _global_container


def configure_services(container: Container) -> None:
    """
    Configure all application services in the container.
    
    Args:
        container: Container to configure
    """
    from config.settings import get_agent_configs, get_llm_config
    from src.models.agent import AgentConfig
    from src.core.agent import Agent
    from src.services.llm_service import LLMService
    from src.services.orchestrator import AgentOrchestrator
    from src.core.prompt_loader import FilePromptLoader, get_prompt_loader
    from src.core.planner import TaskPlanner
    from src.core.synthesizer import AnswerSynthesizer
    from src.tools.registry import get_tool_registry
    
    logger.info("Configuring application services...")
    
    # Register prompt loader as singleton
    container.register_singleton(
        FilePromptLoader,
        instance=get_prompt_loader()
    )
    
    # Register tool registry as singleton
    container.register_singleton(
        type(get_tool_registry()),
        instance=get_tool_registry()
    )
    
    # Register LLM service factory
    def create_llm_service() -> LLMService:
        llm_config = get_llm_config()
        agent_config = AgentConfig(
            base_url=llm_config["base_url"],
            api_key=llm_config["api_key"],
            model=llm_config["model"],
            search_url="",
            max_search_results=5,
            max_retries=llm_config["max_retries"],
            temperature=0.3,
            top_p=0.9
        )
        return LLMService(agent_config)
    
    container.register_transient(LLMService, factory=create_llm_service)

    # Register other services
    container.register_transient(TaskPlanner, implementation=TaskPlanner)

    def create_synthesizer() -> AnswerSynthesizer:
        llm_service = container.resolve(LLMService)
        prompt_loader = container.resolve(FilePromptLoader)
        return AnswerSynthesizer(llm_service, prompt_loader)

    container.register_transient(AnswerSynthesizer, factory=create_synthesizer)

    def create_agent_config(temperature: float, top_p: float) -> AgentConfig:
        llm_config = get_llm_config()
        return AgentConfig(
            base_url=llm_config["base_url"],
            api_key=llm_config["api_key"],
            model=llm_config["model"],
            search_url="",  # Not used directly by agent
            max_search_results=5,
            max_retries=llm_config["max_retries"],
            temperature=temperature,
            top_p=top_p,
        )

    def create_agent(agent_config: AgentConfig) -> Agent:
        llm_service = container.resolve(LLMService)
        return Agent(agent_config, llm_service)

    def default_agent_configs_provider() -> List[Dict[str, float]]:
        return get_agent_configs()

    def create_orchestrator() -> AgentOrchestrator:
        synthesizer = container.resolve(AnswerSynthesizer)
        return AgentOrchestrator(
            synthesizer=synthesizer,
            agent_config_factory=create_agent_config,
            agent_factory=create_agent,
            default_agent_configs_provider=default_agent_configs_provider,
        )

    container.register_singleton(AgentOrchestrator, factory=create_orchestrator)
    
    logger.info("Service configuration completed")


def initialize_container() -> Container:
    """
    Initialize and configure the global container.
    
    Returns:
        Configured container
    """
    container = get_container()

    # Avoid re-registering services if the container is already configured
    if not container.get_registered_services():
        configure_services(container)

    return container
