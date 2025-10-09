"""
Configuration settings for Heavy AI application.
Uses Pydantic Settings for validation and type safety.
"""
import os
from typing import List, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings


class AgentConfigModel(BaseSettings):
    """Configuration for individual agents"""
    temperature: float = Field(..., description="Temperature setting for the agent")
    top_p: float = Field(..., description="Top-p setting for the agent")


class Settings(BaseSettings):
    """Main application settings"""
    
    # Core API settings - preserve existing values
    BASE_URL: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="Base URL for the LLM API"
    )
    MODEL: str = Field(
        default="qwen/qwen3-235b-a22b", 
        description="Model name to use"
    )
    SEARCH_API_URL: str = Field(
        default="http://localhost:8888/search",
        description="URL for the search API"
    )
    
    # API configuration
    API_KEY: str = Field(..., description="API key for LLM service")
    MAX_SEARCH_RESULTS: int = Field(default=5, description="Maximum search results to return")
    MAX_RETRIES_PER_STEP: int = Field(default=3, description="Maximum retries per agent step")
    
    # Flask configuration
    FLASK_SECRET_KEY: str = Field(..., description="Secret key for Flask sessions")
    FLASK_PORT: int = Field(default=5000, description="Port for Flask application")
    FLASK_DEBUG: bool = Field(default=False, description="Enable Flask debug mode")
    
    # Agent configurations - preserve existing settings
    AGENT_CONFIGS: List[Dict[str, float]] = Field(
        default=[
            {"temperature": 0.01, "top_p": 0.01},
            {"temperature": 1.0, "top_p": 1.0}
        ],
        description="Configuration for multiple agents"
    )
    
    # Logging configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")
    
    # Environment
    ENVIRONMENT: str = Field(default="development", description="Application environment")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance"""
    return settings


def get_agent_configs() -> List[Dict[str, float]]:
    """Get agent configurations"""
    return settings.AGENT_CONFIGS


def get_llm_config() -> Dict[str, Any]:
    """Get LLM service configuration"""
    return {
        "base_url": settings.BASE_URL,
        "api_key": settings.API_KEY,
        "model": settings.MODEL,
        "max_retries": settings.MAX_RETRIES_PER_STEP
    }


def get_search_config() -> Dict[str, Any]:
    """Get search service configuration"""
    return {
        "url": settings.SEARCH_API_URL,
        "max_results": settings.MAX_SEARCH_RESULTS
    }