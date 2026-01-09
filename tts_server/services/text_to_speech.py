from collections.abc import AsyncIterator
from uuid import UUID

from tts_server.domain.models import TTSRequest, TTSResponse, VoiceModel
from tts_server.ports.repository import VoiceRepositoryPort
from tts_server.ports.tts import TTSPort


class TextToSpeechService:
    def __init__(
        self,
        tts_adapter: TTSPort,
        voice_repository: VoiceRepositoryPort,
    ) -> None:
        self._tts = tts_adapter
        self._voices = voice_repository

    async def synthesize(
        self,
        text: str,
        language: str,
        speed: float,
        voice_id: UUID | None = None,
    ) -> TTSResponse:

        voice: VoiceModel | None = None
        if voice_id:
            voice = await self._voices.get(voice_id)
        
        request = TTSRequest(
            text=text,
            voice_id=voice_id,
            language=language,
            speed=speed,
        )
        
        return await self._tts.synthesize(request, voice)

    async def synthesize_stream(
        self,
        text: str,
        language: str,
        speed: float,
        voice_id: UUID | None = None,
    ) -> AsyncIterator[bytes]:

        voice: VoiceModel | None = None
        if voice_id:
            voice = await self._voices.get(voice_id)
        
        request = TTSRequest(
            text=text,
            voice_id=voice_id,
            language=language,
            speed=speed,
        )
        
        async for chunk in self._tts.synthesize_stream(request, voice):
            yield chunk

    async def get_available_voices(self) -> list[str]:
        return await self._tts.get_available_voices()

    async def get_supported_languages(self) -> list[str]:
        return await self._tts.get_supported_languages()