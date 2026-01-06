"""Application settings using Pydantic."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def yaml_config_settings_source(settings: "Settings") -> dict[str, Any]:
    """Load settings from config.yml file."""
    config_path = Path("config.yml")
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


class TTSSettings(BaseSettings):
    """TTS adapter configuration."""
    
    model_name: str = Field(
        default="tts_models/en/ljspeech/tacotron2-DDC",
        description="Coqui TTS model identifier",
    )
    device: str = Field(
        default="cpu",
        description="Device to run on (cpu or cuda)",
    )
    gpu: bool = Field(
        default=False,
        description="Whether to use GPU acceleration",
    )


class RepositorySettings(BaseSettings):
    """Voice repository configuration."""
    
    voices_dir: str = Field(
        default="~/.cache/tts-server/voices",
        description="Directory to store voice models",
    )


class ServerSettings(BaseSettings):
    """HTTP server configuration."""
    
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind to",
    )
    port: int = Field(
        default=8000,
        description="Port to listen on",
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload for development",
    )


class Settings(BaseSettings):
    """Root application settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="TTS_",
        env_nested_delimiter="__",
        extra="ignore",
    )
    
    tts: TTSSettings = Field(default_factory=TTSSettings)
    repository: RepositorySettings = Field(default_factory=RepositorySettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple[Any, ...]:
        """Customize settings sources to include YAML config."""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            yaml_config_settings_source,
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.
    
    Returns:
        Settings loaded from config.yml and environment variables.
    """
    return Settings()