"""
Configuration settings for the research agent.

Uses Pydantic Settings to load configuration from environment variables.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via .env file or environment variables.
    """

    # API Keys
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for GPT-4o and embeddings"
    )

    openai_base_url: Optional[str] = Field(
        default=None,
        description="Optional custom base URL for OpenAI API (e.g., for proxies/gateways)"
    )

    tavily_api_key: str = Field(
        default="",
        description="Tavily API key for web search"
    )

    # Vector Store Configuration
    vectorstore_dir: Path = Field(
        default=Path("./data/vectorstore"),
        description="Directory to store/load vector store"
    )

    vectorstore_type: str = Field(
        default="faiss",
        description="Type of vector store (faiss, chroma, etc.)"
    )

    # LLM Configuration
    llm_model: str = Field(
        default="gpt-5-mini",
        description="OpenAI model to use for reasoning"
    )

    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM responses"
    )

    llm_max_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum tokens for LLM responses"
    )

    # Embedding Configuration
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model"
    )

    embedding_dimension: int = Field(
        default=1536,
        gt=0,
        description="Dimension of embeddings"
    )

    # Agent Configuration
    max_steps: int = Field(
        default=10,
        gt=0,
        description="Default maximum steps for agent reasoning loop"
    )

    top_k_results: int = Field(
        default=5,
        gt=0,
        description="Number of top results to retrieve from search"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )

    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def validate_api_keys(self) -> tuple[bool, list[str]]:
        """
        Validate that required API keys are set.

        Returns:
            Tuple of (all_valid, list_of_missing_keys)
        """
        missing = []

        if not self.openai_api_key or self.openai_api_key == "":
            missing.append("OPENAI_API_KEY")

        if not self.tavily_api_key or self.tavily_api_key == "":
            missing.append("TAVILY_API_KEY")

        return len(missing) == 0, missing


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance (singleton pattern).

    Returns:
        Settings instance loaded from environment
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Force reload settings from environment.

    Useful for testing or when environment changes.

    Returns:
        Newly loaded Settings instance
    """
    global _settings
    _settings = Settings()
    return _settings
