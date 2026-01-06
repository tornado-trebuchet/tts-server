"""Coqui TTS adapter implementation."""

import asyncio
import io
import struct
import wave
from collections.abc import AsyncIterator
from typing import Any

from tts_server.domain.models import (
    AudioFormat,
    CloneRequest,
    TTSRequest,
    TTSResponse,
    VoiceModel,
)
from tts_server.ports.tts import TTSPort


class CoquiTTSAdapter(TTSPort):
    """Coqui TTS adapter implementing the TTS port.
    
    Wraps Coqui TTS library for text-to-speech synthesis and voice cloning.
    Uses asyncio.to_thread for CPU-bound operations.
    """

    def __init__(
        self,
        model_name: str = "tts_models/en/ljspeech/tacotron2-DDC",
        device: str = "cpu",
        gpu: bool = False,
    ) -> None:
        """Initialize Coqui TTS adapter.
        
        Args:
            model_name: Coqui TTS model identifier
            device: Device to run on ('cpu' or 'cuda')
            gpu: Whether to use GPU acceleration
        """
        self.model_name = model_name
        self.device = device
        self.gpu = gpu
        self._tts: Any = None  # Lazy load TTS model

    def _get_tts(self) -> Any:
        """Lazy load the TTS model."""
        if self._tts is None:
            from TTS.api import TTS  # type: ignore
            self._tts = TTS(model_name=self.model_name, gpu=self.gpu)
        return self._tts

    def _synthesize_sync(
        self, text: str, language: str, speaker_wav: str | None = None
    ) -> tuple[bytes, int]:
        """Synchronous synthesis returning raw audio and sample rate.
        
        Args:
            text: Text to synthesize
            language: Language code
            speaker_wav: Optional path to speaker reference audio
            
        Returns:
            Tuple of (raw audio bytes, sample rate)
        """
        tts = self._get_tts()
        
        # Synthesize to numpy array
        wav = tts.tts(text=text, language=language, speaker_wav=speaker_wav)
        
        # Get sample rate from config
        sample_rate = tts.synthesizer.output_sample_rate if hasattr(tts, 'synthesizer') else 22050
        
        # Convert numpy array to WAV bytes
        audio_bytes = self._numpy_to_wav_bytes(wav, sample_rate)
        
        return audio_bytes, sample_rate

    def _numpy_to_wav_bytes(self, wav_array: Any, sample_rate: int) -> bytes:
        """Convert numpy audio array to WAV bytes.
        
        Args:
            wav_array: Numpy array of audio samples
            sample_rate: Audio sample rate
            
        Returns:
            WAV file as bytes
        """
        import numpy as np
        
        # Normalize and convert to int16
        wav_array = np.array(wav_array)
        if wav_array.max() <= 1.0:
            wav_array = wav_array * 32767
        wav_array = wav_array.astype(np.int16)
        
        # Write to WAV format in memory
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(wav_array.tobytes())
        
        return buffer.getvalue()

    def _calculate_duration(self, audio_bytes: bytes, sample_rate: int) -> float:
        """Calculate audio duration from WAV bytes."""
        # WAV header is 44 bytes, data is int16 (2 bytes per sample)
        data_size = len(audio_bytes) - 44
        num_samples = data_size // 2
        return num_samples / sample_rate

    async def synthesize(
        self, request: TTSRequest, voice: VoiceModel | None = None
    ) -> TTSResponse:
        """Synthesize speech from text."""
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

    async def synthesize_stream(
        self, request: TTSRequest, voice: VoiceModel | None = None
    ) -> AsyncIterator[bytes]:
        """Stream synthesized speech chunks.
        
        For now, we synthesize the full audio and chunk it.
        Future: implement true streaming with sentence-level synthesis.
        """
        response = await self.synthesize(request, voice)
        
        # Stream in 4KB chunks
        chunk_size = 4096
        audio = response.audio_data
        
        for i in range(0, len(audio), chunk_size):
            yield audio[i:i + chunk_size]

    async def clone_voice(self, request: CloneRequest) -> VoiceModel:
        """Create a cloned voice from audio samples.
        
        Note: Coqui TTS uses speaker reference at synthesis time,
        so this creates a VoiceModel with the first sample saved.
        The actual cloning happens during synthesis.
        """
        import tempfile
        from uuid import uuid4
        
        # For Coqui, we need to save the reference audio
        # The model extracts speaker embedding at synthesis time
        voice_id = uuid4()
        
        # Save first audio sample temporarily to get speaker characteristics
        # In production, you'd combine samples for better quality
        temp_path = tempfile.mktemp(suffix=".wav")
        with open(temp_path, "wb") as f:
            f.write(request.audio_samples[0])
        
        return VoiceModel(
            id=voice_id,
            name=request.name,
            description=request.description,
            language=request.language,
            file_path=temp_path,  # Will be updated by repository when persisted
            metadata={"num_samples": len(request.audio_samples)},
        )

    async def get_available_voices(self) -> list[str]:
        """Get list of built-in voice names."""
        tts = await asyncio.to_thread(self._get_tts)
        
        # Return available speakers if multi-speaker model
        if hasattr(tts, 'speakers') and tts.speakers:
            return list(tts.speakers)
        
        return ["default"]

    async def get_supported_languages(self) -> list[str]:
        """Get list of supported language codes."""
        tts = await asyncio.to_thread(self._get_tts)
        
        if hasattr(tts, 'languages') and tts.languages:
            return list(tts.languages)
        
        # Default to English if model doesn't specify
        return ["en"]
