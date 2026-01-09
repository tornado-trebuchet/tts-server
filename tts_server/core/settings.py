from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def yaml_config_settings_source(settings: Any) -> dict[str, Any]:
    config_path = Path("config.yml")
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


class TTSSettings(BaseSettings):    
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
    
    voices_dir: str = Field(
        default="~/.cache/tts-server/voices",
        description="Directory to store voice models",
    )
    metadata_file: str = Field(
        default="metadata.json",
        description="Filename for repository metadata index",
    )
    voice_extension: str = Field(
        default=".voice",
        description="File extension used for stored voice data",
    )


class ServerSettings(BaseSettings):
    
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


class AudioSettings(BaseSettings):
    
    device_index: int | None = Field(
        default=None,
        description="Output device index (None = system default)",
    )
    buffer_size: int = Field(
        default=2048,
        description="Audio buffer size in frames",
    )
    default_sample_rate: int = Field(
        default=22050,
        description="Default sample rate for audio playback",
    )
    default_channels: int = Field(
        default=1,
        description="Default number of audio channels",
    )


class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(
        env_prefix="TTS_",
        env_nested_delimiter="__",
        extra="ignore",
    )
    
    tts: TTSSettings = Field(default_factory=TTSSettings)
    repository: RepositorySettings = Field(default_factory=RepositorySettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    
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
            lambda: yaml_config_settings_source(cls),
            file_secret_settings,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()