import asyncio
import os
import tempfile
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

import numpy as np
from TTS.api import TTS  # type: ignore

from tts_server.domain.models import (
    AudioFormat,
    CloneRequest,
    TTSRequest,
    TTSResponse,
    VoiceModel,
)
from tts_server.ports.tts import TTSPort


class CoquiTTSAdapter(TTSPort):
    def __init__(
        self,
        model_name: str,
        gpu: bool,
    ) -> None:
        self.model_name = model_name
        self.gpu = gpu
        self.tts: Any = TTS(model_name=self.model_name, gpu=self.gpu)

    def _normalize(self, text: str) -> str:
        normalized = text.encode("ascii", errors="ignore").decode("ascii")
        normalized = " ".join(normalized.split())
        
        return normalized.strip()

    def _synthesize_sync(
        self, text: str, language: str, speaker_wav: str | None = None
    ) -> tuple[bytes, int]:
        normalized_text = self._normalize(text)
        
        if not normalized_text:
            raise ValueError("Text is empty after normalization (contains only unsupported characters)")
        
        tts_kwargs = {"text": normalized_text, "speaker_wav": speaker_wav}
        if self.tts.is_multi_lingual:
            tts_kwargs["language"] = language
        wav = self.tts.tts(**tts_kwargs)
        
        if hasattr(self.tts, "synthesizer"):
            sample_rate = self.tts.synthesizer.output_sample_rate
        else:
            sample_rate = 22050
        audio_bytes = self._numpy_to_pcm_bytes(wav)
        
        return audio_bytes, sample_rate

    def _numpy_to_pcm_bytes(self, wav_array: Any) -> bytes:
        """Convert numpy array to raw 16-bit PCM bytes."""
        wav_array = np.array(wav_array)
        if wav_array.max() <= 1.0:
            wav_array = wav_array * 32767
        wav_array = wav_array.astype(np.int16)
        
        result: bytes = wav_array.tobytes()
        return result

    def _calculate_duration(self, audio_bytes: bytes, sample_rate: int) -> float:
        """Calculate audio duration from raw PCM bytes."""
        num_samples = len(audio_bytes) // 2  # 2 bytes per sample (int16)
        return num_samples / sample_rate

    async def synthesize(
        self, request: TTSRequest, voice: VoiceModel | None = None
    ) -> TTSResponse:
        speaker_wav = voice.file_path if voice else None
        
        audio_bytes, sample_rate = await asyncio.to_thread(
            self._synthesize_sync,
            request.text,
            request.language,
            speaker_wav,
        )
        
        duration = self._calculate_duration(audio_bytes, sample_rate)
        
        return TTSResponse(
            audio_data=audio_bytes,
            audio_format=AudioFormat.WAV,
            sample_rate=sample_rate,
            duration_seconds=duration,
            channels=1,
        )

    # TODO: implement 
    async def synthesize_stream(
        self, request: TTSRequest, voice: VoiceModel | None = None
    ) -> AsyncIterator[bytes]:
        response = await self.synthesize(request, voice)
        
        chunk_size = 4096
        audio = response.audio_data
        
        for i in range(0, len(audio), chunk_size):
            yield audio[i:i + chunk_size]

    async def clone_voice(self, request: CloneRequest) -> VoiceModel:
        voice_id = uuid4()

        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        with open(temp_path, "wb") as f:
            f.write(request.audio_samples[0])

        return VoiceModel(
            id=voice_id,
            name=request.name,
            description=request.description,
            language=request.language,
            file_path=temp_path,
            metadata={"num_samples": len(request.audio_samples)},
        )

    async def get_available_voices(self) -> list[str]:
        if hasattr(self.tts, 'speakers') and self.tts.speakers:
            return list(self.tts.speakers)
        
        return ["default"]

    async def get_supported_languages(self) -> list[str]:
        if hasattr(self.tts, 'languages') and self.tts.languages:
            return list(self.tts.languages)
        
        return ["en"]
