"""Voice cloning service for creating custom voices."""

from uuid import UUID

from tts_server.domain.models import CloneRequest, VoiceModel
from tts_server.ports.repository import VoiceRepositoryPort
from tts_server.ports.tts import TTSPort


class CloneSpeechService:
    """Service for voice cloning operations.
    
    Handles voice creation, storage, and management.
    """

    def __init__(
        self,
        tts_adapter: TTSPort,
        voice_repository: VoiceRepositoryPort,
    ) -> None:
        """Initialize service with adapters.
        
        Args:
            tts_adapter: TTS adapter for voice cloning
            voice_repository: Repository for voice model storage
        """
        self._tts = tts_adapter
        self._voices = voice_repository

    async def clone_voice(
        self,
        name: str,
        audio_samples: list[bytes],
        description: str = "",
        language: str = "en",
    ) -> VoiceModel:
        """Create and store a cloned voice.
        
        Args:
            name: Name for the voice
            audio_samples: Audio sample files as bytes
            description: Voice description
            language: Language code
            
        Returns:
            Created and persisted voice model
        """
        request = CloneRequest(
            name=name,
            audio_samples=audio_samples,
            description=description,
            language=language,
        )
        
        # Clone voice using TTS adapter
        voice = await self._tts.clone_voice(request)
        
        # Persist voice with first audio sample as reference
        # (Coqui uses speaker audio at synthesis time)
        voice = await self._voices.save(voice, audio_samples[0])
        
        return voice

    async def get_voice(self, voice_id: UUID) -> VoiceModel | None:
        """Get a stored voice by ID."""
        return await self._voices.get(voice_id)

    async def list_voices(self) -> list[VoiceModel]:
        """List all stored cloned voices."""
        return await self._voices.list_all()

    async def delete_voice(self, voice_id: UUID) -> bool:
        """Delete a stored voice."""
        return await self._voices.delete(voice_id)

    async def voice_exists(self, voice_id: UUID) -> bool:
        """Check if a voice exists."""
        return await self._voices.exists(voice_id)