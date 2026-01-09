from uuid import UUID

from tts_server.domain.models import CloneRequest, VoiceModel
from tts_server.ports.clone_voice import VoiceCloningPort
from tts_server.ports.repository import VoiceRepositoryPort


class CloneSpeechService:

    def __init__(
        self,
        tts_adapter: VoiceCloningPort,
        voice_repository: VoiceRepositoryPort,
    ) -> None:
        
        self._tts = tts_adapter
        self._voices = voice_repository

    async def clone_voice(
        self,
        name: str,
        audio_samples: list[bytes],
        description: str = "",
        language: str = "en",
    ) -> VoiceModel:

        request = CloneRequest(
            name=name,
            audio_samples=audio_samples,
            description=description,
            language=language,
        )
        
        voice = await self._tts.clone_voice(request)
        voice = await self._voices.save(voice, audio_samples[0])
        
        return voice

    async def get_voice(self, voice_id: UUID) -> VoiceModel | None:
        return await self._voices.get(voice_id)

    async def list_voices(self) -> list[VoiceModel]:
        return await self._voices.list_all()

    async def delete_voice(self, voice_id: UUID) -> bool:
        return await self._voices.delete(voice_id)

    async def voice_exists(self, voice_id: UUID) -> bool:
        return await self._voices.exists(voice_id)