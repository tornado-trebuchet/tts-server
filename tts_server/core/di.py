"""Dependency injection wiring - pure Python factory functions."""

from functools import lru_cache

from tts_server.adapters.repository.repository import FileVoiceRepository
from tts_server.adapters.tts.coqui import CoquiTTSAdapter
from tts_server.core.settings import Settings, get_settings
from tts_server.ports.repository import VoiceRepositoryPort
from tts_server.ports.tts import TTSPort
from tts_server.services.clone_speech import CloneSpeechService
from tts_server.services.text_to_speech import TextToSpeechService


@lru_cache
def get_voice_repository(settings: Settings | None = None) -> VoiceRepositoryPort:
    """Create and cache voice repository instance.
    
    Args:
        settings: Application settings (uses cached settings if None)
        
    Returns:
        Configured voice repository adapter
    """
    if settings is None:
        settings = get_settings()
    return FileVoiceRepository(voices_dir=settings.repository.voices_dir)


@lru_cache
def get_tts_adapter(settings: Settings | None = None) -> TTSPort:
    """Create and cache TTS adapter instance.
    
    Args:
        settings: Application settings (uses cached settings if None)
        
    Returns:
        Configured TTS adapter
    """
    if settings is None:
        settings = get_settings()
    return CoquiTTSAdapter(
        model_name=settings.tts.model_name,
        device=settings.tts.device,
        gpu=settings.tts.gpu,
    )


def get_tts_service(
    tts_adapter: TTSPort | None = None,
    voice_repository: VoiceRepositoryPort | None = None,
) -> TextToSpeechService:
    """Create text-to-speech service.
    
    Args:
        tts_adapter: TTS adapter (uses cached default if None)
        voice_repository: Voice repository (uses cached default if None)
        
    Returns:
        Configured TTS service
    """
    if tts_adapter is None:
        tts_adapter = get_tts_adapter()
    if voice_repository is None:
        voice_repository = get_voice_repository()
    return TextToSpeechService(
        tts_adapter=tts_adapter,
        voice_repository=voice_repository,
    )


def get_clone_service(
    tts_adapter: TTSPort | None = None,
    voice_repository: VoiceRepositoryPort | None = None,
) -> CloneSpeechService:
    """Create voice cloning service.
    
    Args:
        tts_adapter: TTS adapter (uses cached default if None)
        voice_repository: Voice repository (uses cached default if None)
        
    Returns:
        Configured clone service
    """
    if tts_adapter is None:
        tts_adapter = get_tts_adapter()
    if voice_repository is None:
        voice_repository = get_voice_repository()
    return CloneSpeechService(
        tts_adapter=tts_adapter,
        voice_repository=voice_repository,
    )


class Container:
    """Simple DI container for accessing services.
    
    Provides a centralized access point for all application services.
    """
    
    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize container with settings.
        
        Args:
            settings: Application settings (uses cached settings if None)
        """
        self._settings = settings or get_settings()
    
    @property
    def settings(self) -> Settings:
        """Get application settings."""
        return self._settings
    
    @property
    def voice_repository(self) -> VoiceRepositoryPort:
        """Get voice repository instance."""
        return get_voice_repository(self._settings)
    
    @property
    def tts_adapter(self) -> TTSPort:
        """Get TTS adapter instance."""
        return get_tts_adapter(self._settings)
    
    @property
    def tts_service(self) -> TextToSpeechService:
        """Get TTS service instance."""
        return get_tts_service(self.tts_adapter, self.voice_repository)
    
    @property
    def clone_service(self) -> CloneSpeechService:
        """Get voice cloning service instance."""
        return get_clone_service(self.tts_adapter, self.voice_repository)


# Global container instance (lazy initialized)
_container: Container | None = None


def get_container() -> Container:
    """Get the global DI container.
    
    Returns:
        Initialized container with all services
    """
    global _container
    if _container is None:
        _container = Container()
    return _container