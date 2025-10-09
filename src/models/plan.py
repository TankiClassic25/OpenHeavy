"""
Plan-related Pydantic models.
Migrated from agent.py to maintain backward compatibility.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class Step(BaseModel):
    """
    Represents a single step in an agent's execution plan.
    Each step contains instructions for a subagent and tool information.
    """
    title: str = Field(..., description="Short description of the step (1-7 words)")
    tool: Optional[str] = Field(None, description="Tool name to use for this step")
    system_prompt: str = Field(..., description="Detailed instructions for the subagent")
    fields_for_subagent: List[str] = Field(
        default_factory=list, 
        description="Fields that the subagent should return"
    )
    report: bool = Field(default=False, description="Whether this is the final report step")


class PlanResponse(BaseModel):
    """
    Response containing the complete execution plan.
    Contains a list of steps that will be executed sequentially.
    """
    plan: List[Step] = Field(..., description="List of steps to execute")
    
    def get_total_steps(self) -> int:
        """Get the total number of steps in the plan"""
        return len(self.plan)
    
    def get_report_step(self) -> Optional[Step]:
        """Get the step marked as report step"""
        for step in self.plan:
            if step.report:
                return step
        return None
    
    def mark_last_as_report(self) -> None:
        """Mark the last step as the report step"""
        if self.plan:
            # Reset all report flags
            for step in self.plan:
                step.report = False
            # Mark last step as report
            self.plan[-1].report = True