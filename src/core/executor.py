"""
Plan executor component for executing individual steps.
Extracts execution logic from the original Agent class while preserving behavior.
"""
import json
import time
from typing import Dict, Any, List, Optional
from src.core.interfaces import BasePlanExecutor, ILLMService
from src.models.plan import Step, PlanResponse
from src.models.agent import AgentConfig
from src.exceptions.agent import ExecutionError, MaxRetriesExceededError
from src.tools.registry import get_tool_registry
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class PlanExecutor(BasePlanExecutor):
    """
    Executes individual steps in an agent's plan.
    Preserves the exact same execution logic as Agent.run_subagent().
    """
    
    def __init__(self, llm_service: ILLMService, agent_config: AgentConfig):
        """
        Initialize the plan executor.
        
        Args:
            llm_service: LLM service for step execution
            agent_config: Agent configuration
        """
        super().__init__(llm_service, agent_config)
        self.tool_registry = get_tool_registry()
    
    def execute_step(self, step: Step, context: str) -> str:
        """
        Execute a single step in the plan.
        Preserves the exact same logic as Agent.run_subagent().
        
        Args:
            step: Step to execute
            context: Execution context (previous results, user request)
            
        Returns:
            Step execution result as string
            
        Raises:
            ExecutionError: If step execution fails
            MaxRetriesExceededError: If max retries exceeded
        """
        try:
            logger.debug(f"Executing step: {step.title}")
            
            # Build system content - preserve original format
            system_content = f"{step.system_prompt}\n\n"
            system_content += "CRITICAL: TEXT-ONLY output. No images/graphics. Use tables/lists.\n"
            system_content += self._get_datetime_context()
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": context}
            ]
            
            # Get available tools for this execution
            tool_definitions = self.tool_registry.get_tool_definitions()
            
            step_output = None
            retries = 0
            
            # Retry loop - preserve original retry logic
            while retries <= self.agent_config.max_retries:
                try:
                    completion = self.llm_service.create_completion(
                        messages=messages,
                        tools=tool_definitions,
                        tool_choice="auto",
                        temperature=self.agent_config.temperature,
                        top_p=self.agent_config.top_p
                    )
                    
                    message = completion.choices[0].message
                    tool_calls = getattr(message, "tool_calls", None)
                    
                    # Handle tool calls - preserve original logic
                    if tool_calls:
                        for call in tool_calls:
                            func = getattr(call, "function", None)
                            func_name = getattr(func, "name", None) if func else getattr(call, "name", None)
                            args_raw = getattr(func, "arguments", None) if func else getattr(call, "arguments", None)
                            
                            try:
                                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                            except:
                                args = args_raw
                            
                            result = self._execute_tool(func_name, args or {})
                            
                            if func_name == "final_response":
                                step_output = result
                                break
                            
                            # Add tool call and result to conversation
                            messages.append({
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [call]
                            })
                            
                            if result is not None:
                                messages.append({
                                    "role": "tool",
                                    "name": func_name,
                                    "content": json.dumps(result)
                                })
                        
                        if step_output is not None:
                            break
                        continue
                    
                    # Handle direct message content
                    if message.content:
                        retries += 1
                        if retries <= self.agent_config.max_retries:
                            messages.append({"role": "assistant", "content": message.content})
                            messages.append({
                                "role": "user",
                                "content": "Error: Use final_response tool to return result."
                            })
                            continue
                        else:
                            step_output = message.content
                            break
                    
                    # Handle empty response
                    retries += 1
                    if retries > self.agent_config.max_retries:
                        step_output = json.dumps({"error": "no_response", "step": step.title})
                        break
                    else:
                        messages.append({
                            "role": "user",
                            "content": "Error: Empty response. Use final_response tool."
                        })
                
                except Exception as e:
                    retries += 1
                    if retries > self.agent_config.max_retries:
                        raise ExecutionError(
                            f"Step execution failed after {retries} retries: {str(e)}",
                            step_title=step.title,
                            cause=e
                        )
                    
                    logger.warning(f"Step execution attempt {retries} failed: {str(e)}")
                    time.sleep(0.5)  # Brief delay before retry
            
            if step_output is None:
                raise MaxRetriesExceededError(
                    f"Step '{step.title}' failed after {self.agent_config.max_retries} retries",
                    max_retries=self.agent_config.max_retries,
                    operation=f"execute_step_{step.title}"
                )
            
            logger.debug(f"Step '{step.title}' completed successfully")
            return step_output
            
        except (ExecutionError, MaxRetriesExceededError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error in step execution: {str(e)}")
            raise ExecutionError(
                f"Unexpected error executing step '{step.title}': {str(e)}",
                step_title=step.title,
                cause=e
            )
    
    def execute_plan(
        self, 
        plan: PlanResponse, 
        user_task: str,
        progress_callback: Optional[callable] = None
    ) -> List[str]:
        """
        Execute a complete plan step by step.
        
        Args:
            plan: Plan to execute
            user_task: Original user task
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of step results
        """
        history = []
        
        for idx, step in enumerate(plan.plan):
            # Build context for this step
            user_msg = self._build_step_context(plan, idx, history, user_task)
            
            # Execute the step
            step_output = self.execute_step(step, user_msg)
            history.append(step_output)
            
            # Call progress callback if provided
            if progress_callback:
                progress = round(((idx + 1) / len(plan.plan)) * 100)
                progress_callback(idx + 1, len(plan.plan), progress)
            
            # If this is the report step, we can return early
            if step.report:
                logger.info(f"Plan execution completed at report step {idx + 1}")
                return history
        
        logger.info(f"Plan execution completed with {len(history)} steps")
        return history
    
    def _execute_tool(self, func_name: str, args: Dict[str, Any]) -> Any:
        """
        Execute a tool by name with given arguments.
        Preserves the exact same logic as Agent._execute_tool().
        
        Args:
            func_name: Name of the tool to execute
            args: Tool arguments
            
        Returns:
            Tool execution result
        """
        try:
            if func_name == "final_response":
                # Handle final_response specially - preserve original behavior
                return args.get("content") if isinstance(args, dict) else args
            
            # Execute tool through registry
            result = self.tool_registry.execute_tool(func_name, **args)
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {func_name} - {str(e)}")
            return {"content": f"Error in {func_name}: {str(e)}"}
    
    def _build_step_context(
        self, 
        plan: PlanResponse, 
        idx: int, 
        history: List[str], 
        user_task: str
    ) -> str:
        """
        Build context for step execution.
        Preserves the exact same logic as Agent._build_step_context().
        
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
    
    def _get_datetime_context(self) -> str:
        """
        Get current datetime context.
        Preserves the exact same format as the original implementation.
        
        Returns:
            Formatted datetime string
        """
        return f"Current date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"