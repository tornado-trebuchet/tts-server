from tts_server.adapters.repository.repository import FileVoiceRepository
from tts_server.adapters.tts.coqui import CoquiTTSAdapter
from tts_server.core.settings import Settings, get_settings
from tts_server.ports.repository import VoiceRepositoryPort
from tts_server.ports.tts import TTSPort
from tts_server.services.clone_speech import CloneSpeechService
from tts_server.services.text_to_speech import TextToSpeechService


def get_voice_repository(settings: Settings | None = None) -> VoiceRepositoryPort:
    if settings is None:
        settings = get_settings()
    return FileVoiceRepository(
        voices_dir=settings.repository.voices_dir,
        metadata_file=settings.repository.metadata_file,
        voice_extension=settings.repository.voice_extension,
    )


def get_tts_adapter(settings: Settings | None = None) -> TTSPort:
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
    if tts_adapter is None:
        tts_adapter = get_tts_adapter()
    if voice_repository is None:
        voice_repository = get_voice_repository()
    return CloneSpeechService(
        tts_adapter=tts_adapter,
        voice_repository=voice_repository,
    )


class Container:
    
    def __init__(self, settings: Settings | None = None) -> None:
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


_container: Container | None = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container