"""
Answer synthesizer component for combining multiple agent results.
Extracts synthesis logic from the original app.py while preserving behavior.
"""
import time
from typing import List, Dict, Any, Optional, Generator
from src.core.interfaces import BaseAnswerSynthesizer, ILLMService, IPromptLoader
from src.exceptions.agent import SynthesisError
from src.core.prompt_loader import load_prompt_with_variables
import logging


logger = logging.getLogger(__name__)


class AnswerSynthesizer(BaseAnswerSynthesizer):
    """
    Synthesizes final answers from multiple agent results.
    Preserves the exact same synthesis logic as app.py select_best_answer().
    """
    
    def __init__(self, llm_service: ILLMService, prompt_loader: IPromptLoader):
        """
        Initialize the answer synthesizer.
        
        Args:
            llm_service: LLM service for synthesis
            prompt_loader: Prompt loader for system prompts
        """
        super().__init__(llm_service, prompt_loader)
    
    def synthesize_answer(
        self, 
        user_query: str, 
        agent_results: List[str]
    ) -> str:
        """
        Synthesize a final answer from multiple agent results.
        Preserves the exact same logic as app.py select_best_answer().
        
        Args:
            user_query: Original user query
            agent_results: Results from multiple agents
            
        Returns:
            Synthesized final answer
            
        Raises:
            SynthesisError: If synthesis fails
        """
        try:
            if not agent_results:
                raise SynthesisError(
                    "Cannot synthesize answer: no agent results provided",
                    agent_count=0,
                    successful_agents=0
                )
            
            logger.info(f"Synthesizing answer from {len(agent_results)} agent results")
            
            # Combine agent responses - preserve original format
            combined_responses = "\n\n---\n\n".join([
                f"Agent {i+1} response:\n{response}" 
                for i, response in enumerate(agent_results)
            ])
            
            # Load and format the synthesizer prompt
            system_prompt = load_prompt_with_variables(
                "synthesizer_prompt",
                {
                    "user_query": user_query,
                    "agent_responses": combined_responses
                }
            )
            
            # Create completion - preserve original parameters
            completion = self.llm_service.create_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Provide the best synthesized answer as a detailed MARKDOWN report."}
                ],
                stream=False,  # Non-streaming version for simple synthesis
                temperature=0.3
            )
            
            # Extract the synthesized content
            if hasattr(completion.choices[0].message, 'content'):
                synthesized_answer = completion.choices[0].message.content
            else:
                raise SynthesisError(
                    "LLM did not return content in synthesis response",
                    agent_count=len(agent_results),
                    successful_agents=len(agent_results)
                )
            
            if not synthesized_answer or not synthesized_answer.strip():
                raise SynthesisError(
                    "LLM returned empty synthesis result",
                    agent_count=len(agent_results),
                    successful_agents=len(agent_results)
                )
            
            logger.info("Answer synthesis completed successfully")
            return synthesized_answer.strip()
            
        except SynthesisError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Answer synthesis failed: {str(e)}")
            raise SynthesisError(
                f"Failed to synthesize answer: {str(e)}",
                agent_count=len(agent_results) if agent_results else 0,
                successful_agents=len(agent_results) if agent_results else 0,
                cause=e
            )
    
    def synthesize_answer_streaming(
        self, 
        user_query: str, 
        agent_results: List[str],
        chunk_callback: Optional[callable] = None
    ) -> Generator[str, None, None]:
        """
        Synthesize answer with streaming output.
        Preserves the exact same streaming logic as the original implementation.
        
        Args:
            user_query: Original user query
            agent_results: Results from multiple agents
            chunk_callback: Optional callback for each chunk
            
        Yields:
            Chunks of the synthesized answer
            
        Raises:
            SynthesisError: If synthesis fails
        """
        try:
            if not agent_results:
                raise SynthesisError(
                    "Cannot synthesize answer: no agent results provided",
                    agent_count=0,
                    successful_agents=0
                )
            
            logger.info(f"Starting streaming synthesis from {len(agent_results)} agent results")
            
            # Combine agent responses - preserve original format
            combined_responses = "\n\n---\n\n".join([
                f"Agent {i+1} response:\n{response}" 
                for i, response in enumerate(agent_results)
            ])
            
            # Load and format the synthesizer prompt
            system_prompt = load_prompt_with_variables(
                "synthesizer_prompt",
                {
                    "user_query": user_query,
                    "agent_responses": combined_responses
                }
            )
            
            # Create streaming completion - preserve original parameters
            stream_response = self.llm_service.create_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Provide the best synthesized answer as a detailed MARKDOWN report."}
                ],
                stream=True,
                temperature=0.3
            )
            
            # Stream the response chunks
            for chunk in stream_response:
                if chunk.choices[0].delta.content:
                    chunk_content = chunk.choices[0].delta.content
                    
                    # Call callback if provided
                    if chunk_callback:
                        chunk_callback(chunk_content)
                    
                    yield chunk_content
                    
                    # Add delay to match original behavior
                    time.sleep(0.05)
            
            logger.info("Streaming synthesis completed successfully")
            
        except SynthesisError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Streaming synthesis failed: {str(e)}")
            raise SynthesisError(
                f"Failed to synthesize streaming answer: {str(e)}",
                agent_count=len(agent_results) if agent_results else 0,
                successful_agents=len(agent_results) if agent_results else 0,
                cause=e
            )
    
    def validate_agent_results(self, agent_results: List[str]) -> Dict[str, Any]:
        """
        Validate and analyze agent results before synthesis.
        
        Args:
            agent_results: Results from agents
            
        Returns:
            Dictionary with validation results and statistics
        """
        validation_result = {
            "total_results": len(agent_results),
            "valid_results": 0,
            "empty_results": 0,
            "error_results": 0,
            "average_length": 0,
            "issues": []
        }
        
        if not agent_results:
            validation_result["issues"].append("No agent results provided")
            return validation_result
        
        total_length = 0
        
        for i, result in enumerate(agent_results):
            if not result or not result.strip():
                validation_result["empty_results"] += 1
                validation_result["issues"].append(f"Agent {i+1} returned empty result")
                continue
            
            if "error" in result.lower() and len(result) < 100:
                validation_result["error_results"] += 1
                validation_result["issues"].append(f"Agent {i+1} may have returned an error")
                continue
            
            validation_result["valid_results"] += 1
            total_length += len(result)
        
        if validation_result["valid_results"] > 0:
            validation_result["average_length"] = total_length // validation_result["valid_results"]
        
        # Add warnings for potential issues
        if validation_result["valid_results"] == 0:
            validation_result["issues"].append("No valid agent results for synthesis")
        elif validation_result["valid_results"] < len(agent_results) / 2:
            validation_result["issues"].append("More than half of agent results are invalid")
        
        return validation_result
    
    def get_synthesis_summary(
        self, 
        user_query: str, 
        agent_results: List[str],
        synthesized_answer: str
    ) -> Dict[str, Any]:
        """
        Get a summary of the synthesis process for logging/debugging.
        
        Args:
            user_query: Original user query
            agent_results: Agent results that were synthesized
            synthesized_answer: Final synthesized answer
            
        Returns:
            Dictionary with synthesis summary
        """
        validation = self.validate_agent_results(agent_results)
        
        return {
            "user_query_length": len(user_query),
            "agent_results_count": len(agent_results),
            "valid_results_count": validation["valid_results"],
            "synthesized_answer_length": len(synthesized_answer),
            "synthesis_ratio": len(synthesized_answer) / sum(len(r) for r in agent_results) if agent_results else 0,
            "validation_issues": validation["issues"]
        }