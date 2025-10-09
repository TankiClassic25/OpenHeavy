"""
Task planner component for creating execution plans.
Extracts planning logic from the original Agent class while preserving behavior.
"""
from datetime import datetime
from typing import Dict, Any
from src.core.interfaces import BasePlanner, ILLMService, IPromptLoader
from src.models.plan import PlanResponse, Step
from src.exceptions.agent import PlanningError
from src.core.prompt_loader import load_prompt_with_variables
import logging


logger = logging.getLogger(__name__)


class TaskPlanner(BasePlanner):
    """
    Creates execution plans from user requests.
    Preserves the exact same planning logic as the original Agent class.
    """
    
    def __init__(self, llm_service: ILLMService, prompt_loader: IPromptLoader):
        """
        Initialize the task planner.
        
        Args:
            llm_service: LLM service for generating plans
            prompt_loader: Prompt loader for system prompts
        """
        super().__init__(llm_service, prompt_loader)
    
    def create_plan(self, user_request: str) -> PlanResponse:
        """
        Create an execution plan for the given user request.
        Preserves the exact same logic as Agent.create_plan().
        
        Args:
            user_request: User's request to plan for
            
        Returns:
            PlanResponse containing the execution steps
            
        Raises:
            PlanningError: If plan creation fails
        """
        try:
            # Build the planner prompt with current datetime
            datetime_context = self._get_datetime_context()
            system_prompt = load_prompt_with_variables(
                "planner_prompt",
                {"datetime_context": datetime_context}
            )
            
            logger.debug(f"Creating plan for request: {user_request[:100]}...")
            
            # Create completion using structured parsing - preserve original behavior
            completion = self.llm_service.create_structured_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_request}
                ],
                response_format=PlanResponse
            )
            
            plan_response = completion.choices[0].message.parsed
            if not plan_response:
                raise PlanningError(
                    "Planner didn't return a valid response",
                    user_request=user_request
                )
            
            # Post-process the plan - preserve original logic
            if plan_response.plan:
                # Reset all report flags first
                for step in plan_response.plan:
                    step.report = False
                
                # Mark last step as report step
                plan_response.plan[-1].report = True
                
                # Ensure last step includes markdown generation instruction
                last_step = plan_response.plan[-1]
                if "markdown" not in last_step.system_prompt.lower():
                    last_step.system_prompt += (
                        "\n\nGenerate comprehensive MARKDOWN report. "
                        "Use headers, tables, and formatting. TEXT ONLY - no images."
                    )
            
            logger.info(f"Created plan with {len(plan_response.plan)} steps")
            return plan_response
            
        except Exception as e:
            logger.error(f"Plan creation failed: {str(e)}")
            raise PlanningError(
                f"Failed to create execution plan: {str(e)}",
                user_request=user_request,
                cause=e
            )
    
    def _get_datetime_context(self) -> str:
        """
        Get current datetime context for the planner.
        Preserves the exact same format as the original implementation.
        
        Returns:
            Formatted datetime string
        """
        return f"Current date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    def validate_plan(self, plan: PlanResponse) -> bool:
        """
        Validate that a plan meets basic requirements.
        
        Args:
            plan: Plan to validate
            
        Returns:
            True if plan is valid
            
        Raises:
            PlanningError: If plan is invalid
        """
        if not plan.plan:
            raise PlanningError("Plan cannot be empty")
        
        if len(plan.plan) < 1:
            raise PlanningError("Plan must have at least one step")
        
        if len(plan.plan) > 15:
            logger.warning(f"Plan has {len(plan.plan)} steps, which is quite long")
        
        # Check that last step is marked as report
        if not plan.plan[-1].report:
            logger.warning("Last step is not marked as report step")
        
        # Validate each step
        for i, step in enumerate(plan.plan):
            if not step.title:
                raise PlanningError(f"Step {i+1} is missing a title")
            
            if not step.system_prompt:
                raise PlanningError(f"Step {i+1} is missing system prompt")
        
        return True
    
    def get_plan_summary(self, plan: PlanResponse) -> Dict[str, Any]:
        """
        Get a summary of the plan for logging/debugging.
        
        Args:
            plan: Plan to summarize
            
        Returns:
            Dictionary with plan summary
        """
        return {
            "total_steps": len(plan.plan),
            "steps": [
                {
                    "index": i + 1,
                    "title": step.title,
                    "tool": step.tool,
                    "is_report": step.report
                }
                for i, step in enumerate(plan.plan)
            ],
            "report_step_index": next(
                (i + 1 for i, step in enumerate(plan.plan) if step.report),
                None
            )
        }