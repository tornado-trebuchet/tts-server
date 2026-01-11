from tts_server.adapters.audio.sounddevice import SoundDevicePlaybackAdapter
from tts_server.adapters.repository.filesystem import FileVoiceRepository
from tts_server.adapters.tts.coqui import CoquiTTSAdapter
from tts_server.core.settings import Settings, get_settings
from tts_server.ports.audio import AudioPlaybackPort
from tts_server.ports.clone_voice import VoiceCloningPort
from tts_server.ports.repository import VoiceRepositoryPort
from tts_server.ports.tts import TTSPort
from tts_server.services.audio_playback import AudioPlaybackService
from tts_server.services.clone_voice import CloneSpeechService
from tts_server.services.synth_play import SynthPlayService
from tts_server.services.text_to_speech import TextToSpeechService


def get_voice_repository(settings: Settings | None = None) -> VoiceRepositoryPort:
    if settings is None:
        settings = get_settings()
    return FileVoiceRepository(
        voices_dir=settings.repository.voices_dir,
        metadata_file=settings.repository.metadata_file,
        voice_extension=settings.repository.voice_extension,
    )

def get_vc_adapter(settings: Settings | None = None) -> VoiceCloningPort: 
    if settings is None:
        settings = get_settings()
    # TODO: Wire to the separated one
    return CoquiTTSAdapter(
        model_name=settings.tts.model_name,
        gpu=settings.tts.gpu,
    )

def get_tts_adapter(settings: Settings | None = None) -> TTSPort:
    if settings is None:
        settings = get_settings()
    return CoquiTTSAdapter(
        model_name=settings.tts.model_name,
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
    vc_adapter: VoiceCloningPort | None = None,
    voice_repository: VoiceRepositoryPort | None = None,
) -> CloneSpeechService:
    if vc_adapter is None:
        vc_adapter = get_vc_adapter()
    if voice_repository is None:
        voice_repository = get_voice_repository()
    return CloneSpeechService(
        tts_adapter=vc_adapter,
        voice_repository=voice_repository,
    )


def get_audio_adapter(settings: Settings | None = None) -> AudioPlaybackPort:
    if settings is None:
        settings = get_settings()
    return SoundDevicePlaybackAdapter(settings=settings.audio)


def get_audio_service(
    audio_adapter: AudioPlaybackPort | None = None,
) -> AudioPlaybackService:
    if audio_adapter is None:
        audio_adapter = get_audio_adapter()
    return AudioPlaybackService(audio_adapter=audio_adapter)


class Container:
    
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
    
    @property
    def settings(self) -> Settings:
        return self._settings
    
    @property
    def voice_repository(self) -> VoiceRepositoryPort:
        return get_voice_repository(self._settings)
    
    @property
    def tts_adapter(self) -> TTSPort:
        return get_tts_adapter(self._settings)
    
    @property
    def vc_adapter(self) -> VoiceCloningPort:
        return get_vc_adapter(self._settings)

    @property
    def tts_service(self) -> TextToSpeechService:
        return get_tts_service(self.tts_adapter, self.voice_repository)
    
    @property
    def clone_service(self) -> CloneSpeechService:
        return get_clone_service(self.vc_adapter, self.voice_repository)
    
    @property
    def audio_adapter(self) -> AudioPlaybackPort:
        return get_audio_adapter(self._settings)
    
    @property
    def audio_service(self) -> AudioPlaybackService:
        return get_audio_service(self.audio_adapter)

    @property
    def synth_play_service(self) -> SynthPlayService:
        return SynthPlayService(
            tts_adapter=self.tts_adapter,
            audio_adapter=self.audio_adapter,
        )


_container: Container | None = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container