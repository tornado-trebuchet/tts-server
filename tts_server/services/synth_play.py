from collections.abc import Awaitable, Callable

from tts_server.domain.models import (
    PlaybackRequest,
    PlaybackStatus,
    SynthPlayState,
    TTSRequest,
    VoiceModel,
)
from tts_server.ports.audio import AudioPlaybackPort
from tts_server.ports.tts import TTSPort


class SynthPlayService:

    def __init__(
        self,
        tts_adapter: TTSPort,
        audio_adapter: AudioPlaybackPort,
    ) -> None:
        self._tts = tts_adapter
        self._audio = audio_adapter

    async def synthesize_and_play(
        self,
        text: str,
        language: str,
        voice: VoiceModel | None = None,
        on_state_change: Callable[[SynthPlayState, str | None], Awaitable[None]]
        | None = None,
    ) -> PlaybackStatus:

        async def notify(state: SynthPlayState, message: str | None = None) -> None:
            if on_state_change:
                await on_state_change(state, message)

        try:
            await notify(SynthPlayState.SYNTHESIZING, f"Synthesizing: {text[:50]}...")

            tts_request = TTSRequest(
                text=text,
                voice_id=voice.id if voice else None,
                language=language,
            )

            tts_response = await self._tts.synthesize(tts_request, voice)

            await notify(SynthPlayState.PLAYING, "Playing audio...")

            playback_request = PlaybackRequest(
                audio_data=tts_response.audio_data,
                sample_rate=tts_response.sample_rate,
                channels=tts_response.channels,
            )

            playback_status = await self._audio.play(playback_request)

            await notify(SynthPlayState.COMPLETED, "Playback complete")

            return PlaybackStatus(
                is_playing=False,
                duration_seconds=playback_status.duration_seconds,
            )

        except Exception as e:
            await notify(SynthPlayState.ERROR, str(e))
            raise
