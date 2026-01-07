import asyncio
import io
import os
import tempfile
import wave
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

import numpy as np
from TTS.api import TTS

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
        device: str,
        gpu: bool,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.gpu = gpu
        self.tts: Any = TTS(model_name=self.model_name, gpu=self.gpu)


    def _synthesize_sync(
        self, text: str, language: str, speaker_wav: str | None = None
    ) -> tuple[bytes, int]:
        tts_kwargs = {"text": text, "speaker_wav": speaker_wav}
        if self.tts.is_multi_lingual:
            tts_kwargs["language"] = language
        wav = self.tts.tts(**tts_kwargs)
        
        if hasattr(self.tts, "synthesizer"):
            sample_rate = self.tts.synthesizer.output_sample_rate
        else:
            sample_rate = 22050
        audio_bytes = self._numpy_to_wav_bytes(wav, sample_rate)
        
        return audio_bytes, sample_rate

    def _numpy_to_wav_bytes(self, wav_array: Any, sample_rate: int) -> bytes:
        
        wav_array = np.array(wav_array)
        if wav_array.max() <= 1.0:
            wav_array = wav_array * 32767
        wav_array = wav_array.astype(np.int16)
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2) 
            wf.setframerate(sample_rate)
            wf.writeframes(wav_array.tobytes())
        
        return buffer.getvalue()

    def _calculate_duration(self, audio_bytes: bytes, sample_rate: int) -> float:
        data_size = len(audio_bytes) - 44
        num_samples = data_size // 2
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
