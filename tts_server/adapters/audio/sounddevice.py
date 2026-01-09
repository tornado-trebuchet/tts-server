import asyncio
import logging
import wave
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np
import sounddevice as sd

from tts_server.core.settings import AudioSettings
from tts_server.domain.models import PlaybackRequest, PlaybackStatus
from tts_server.ports.audio import AudioPlaybackPort


class SoundDevicePlaybackAdapter(AudioPlaybackPort):

    def __init__(self, settings: AudioSettings) -> None:
        self._settings = settings
        self._lock = Lock()
        self._is_playing = False

    def _play_sync(self, audio_array: np.ndarray[Any, Any], sample_rate: int) -> float:
        with self._lock:
            self._is_playing = True
        try:
            device = self._resolve_output_device()
            sd.play(  # type: ignore
                audio_array,
                samplerate=sample_rate,
                device=device,
                blocksize=self._settings.buffer_size,
            )
            sd.wait()  # type: ignore
            duration = len(audio_array) / sample_rate
            return duration
        finally:
            with self._lock:
                self._is_playing = False

    def _resolve_output_device(self) -> int | None:
        logger = logging.getLogger(__name__)
        if self._settings.device_index is not None:
            logger.debug("Using configured audio device index: %s", self._settings.device_index)
            return self._settings.device_index

        try:
            for i, d in enumerate(sd.query_devices()): # type: ignore
                name = str(d.get("name", "")).lower() 
                if "pulse" in name or "pipewire" in name:
                    logger.debug("Found pulse/pipewire device: %s (index=%d)", d.get("name"), i)
                    return i
        except Exception:
            logger.exception("Error querying sounddevice devices")

        logger.debug("No pulse/pipewire device found, using system default")
        return None

    def _load_wav_file(self, file_path: str) -> tuple[np.ndarray[Any, Any], int, int]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"WAV file not found: {file_path}")
        
        if not path.suffix.lower() == ".wav":
            raise ValueError(f"File must have .wav extension: {file_path}")
        
        with wave.open(file_path, "rb") as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            n_frames = wf.getnframes()
            
            raw_data = wf.readframes(n_frames)
        
        # Determine dtype based on sample width
        if sample_width == 2:
            audio_int = np.frombuffer(raw_data, dtype=np.int16)
            audio_float: np.ndarray[Any, Any] = audio_int.astype(np.float32) / 32768.0
        elif sample_width == 4:
            audio_int = np.frombuffer(raw_data, dtype=np.int32)
            audio_float = audio_int.astype(np.float32) / 2147483648.0
        else:
            raise ValueError(f"Unsupported sample width: {sample_width} bytes")
        
        # Reshape for multi-channel
        if channels > 1:
            audio_float = audio_float.reshape(-1, channels)
        
        return audio_float, sample_rate, channels

    def _parse_audio_data(self, request: PlaybackRequest) -> np.ndarray[Any, Any]:
        # Parse 16-bit PCM audio data
        audio_int16 = np.frombuffer(request.audio_data, dtype=np.int16)
        
        # Reshape for multi-channel if needed
        if request.channels > 1:
            audio_int16 = audio_int16.reshape(-1, request.channels)
        
        # Normalize to float32 for sounddevice
        audio_float32: np.ndarray[Any, Any] = audio_int16.astype(np.float32) / 32768.0
        
        return audio_float32

    async def play(self, request: PlaybackRequest) -> PlaybackStatus:
        audio_array = self._parse_audio_data(request)
        
        duration = await asyncio.to_thread(
            self._play_sync,
            audio_array,
            request.sample_rate,
        )
        
        return PlaybackStatus(
            is_playing=False,
            duration_seconds=duration,
        )

    async def stop(self) -> None:
        await asyncio.to_thread(sd.stop) # type: ignore 
        with self._lock:
            self._is_playing = False

    def is_playing(self) -> bool:
        with self._lock:
            return self._is_playing

    async def play_file(self, file_path: str) -> PlaybackStatus:
        audio_array, sample_rate, _ = self._load_wav_file(file_path)
        
        duration = await asyncio.to_thread(
            self._play_sync,
            audio_array,
            sample_rate,
        )
        
        return PlaybackStatus(
            is_playing=False,
            duration_seconds=duration,
        )