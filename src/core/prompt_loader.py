"""
Prompt loader for loading system prompts from external files.
Allows easy editing of prompts without code changes.
"""
import os
from typing import Dict, Optional
from pathlib import Path
from src.core.interfaces import BasePromptLoader


class FilePromptLoader(BasePromptLoader):
    """
    Loads prompts from text files in the prompts directory.
    Supports template variable substitution.
    """
    
    def __init__(self, prompts_dir: str = "prompts"):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt files
        """
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, str] = {}
        self._cache_enabled = True
    
    def load_prompt(self, prompt_name: str) -> str:
        """
        Load a system prompt by name.
        
        Args:
            prompt_name: Name of the prompt file (without .txt extension)
            
        Returns:
            Prompt content as string
            
        Raises:
            FileNotFoundError: If prompt file is not found
        """
        # Check cache first
        if self._cache_enabled and prompt_name in self._cache:
            return self._cache[prompt_name]
        
        # Construct file path
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        try:
            # Read prompt content
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Cache the content
            if self._cache_enabled:
                self._cache[prompt_name] = content
            
            return content
            
        except Exception as e:
            raise FileNotFoundError(f"Failed to read prompt file {prompt_file}: {str(e)}")
    
    def load_prompt_with_variables(
        self, 
        prompt_name: str, 
        variables: Dict[str, str]
    ) -> str:
        """
        Load a prompt and substitute template variables.
        
        Args:
            prompt_name: Name of the prompt file
            variables: Dictionary of variables to substitute
            
        Returns:
            Prompt with variables substituted
        """
        template = self.load_prompt(prompt_name)
        
        try:
            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing template variable in prompt '{prompt_name}': {e}")
    
    def reload_prompt(self, prompt_name: str) -> str:
        """
        Force reload a prompt from file, bypassing cache.
        
        Args:
            prompt_name: Name of the prompt to reload
            
        Returns:
            Reloaded prompt content
        """
        # Remove from cache if present
        if prompt_name in self._cache:
            del self._cache[prompt_name]
        
        return self.load_prompt(prompt_name)
    
    def clear_cache(self) -> None:
        """Clear the prompt cache"""
        self._cache.clear()
    
    def disable_cache(self) -> None:
        """Disable prompt caching"""
        self._cache_enabled = False
        self.clear_cache()
    
    def enable_cache(self) -> None:
        """Enable prompt caching"""
        self._cache_enabled = True
    
    def list_available_prompts(self) -> list:
        """
        List all available prompt files.
        
        Returns:
            List of prompt names (without .txt extension)
        """
        if not self.prompts_dir.exists():
            return []
        
        prompt_files = []
        for file_path in self.prompts_dir.glob("*.txt"):
            prompt_files.append(file_path.stem)
        
        return sorted(prompt_files)
    
    def prompt_exists(self, prompt_name: str) -> bool:
        """
        Check if a prompt file exists.
        
        Args:
            prompt_name: Name of the prompt to check
            
        Returns:
            True if prompt file exists
        """
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        return prompt_file.exists()


# Global prompt loader instance
_global_prompt_loader: Optional[FilePromptLoader] = None


def get_prompt_loader() -> FilePromptLoader:
    """
    Get the global prompt loader instance.
    
    Returns:
        Global FilePromptLoader instance
    """
    global _global_prompt_loader
    if _global_prompt_loader is None:
        _global_prompt_loader = FilePromptLoader()
    return _global_prompt_loader


def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt using the global prompt loader.
    
    Args:
        prompt_name: Name of the prompt to load
        
    Returns:
        Prompt content
    """
    loader = get_prompt_loader()
    return loader.load_prompt(prompt_name)


def load_prompt_with_variables(prompt_name: str, variables: Dict[str, str]) -> str:
    """
    Load a prompt with variable substitution using the global loader.
    
    Args:
        prompt_name: Name of the prompt to load
        variables: Variables to substitute
        
    Returns:
        Prompt with variables substituted
    """
    loader = get_prompt_loader()
    return loader.load_prompt_with_variables(prompt_name, variables)