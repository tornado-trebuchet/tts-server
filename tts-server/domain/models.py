"""Domain models for TTS server - inputs/outputs for ports and persistence."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class AudioFormat(str, Enum):
    """Supported audio output formats."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"


@dataclass
class TTSRequest:
    """Request for text-to-speech synthesis."""
    text: str
    voice_id: Optional[UUID] = None  # None = use default voice
    language: str = "en"
    audio_format: AudioFormat = AudioFormat.WAV
    speed: float = 1.0


@dataclass
class TTSResponse:
    """Response containing synthesized audio."""
    audio_data: bytes
    audio_format: AudioFormat
    sample_rate: int
    duration_seconds: float


@dataclass
class VoiceModel:
    """A stored voice model for TTS synthesis."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    language: str = "en"
    created_at: datetime = field(default_factory=datetime.now)
    file_path: Optional[str] = None  # Path to voice embedding/model file
    metadata: dict = field(default_factory=dict)  # Adapter-specific metadata


@dataclass
class CloneRequest:
    """Request for voice cloning from audio samples."""
    name: str
    audio_samples: list[bytes]  # Raw audio data from sample files
    description: str = ""
    language: str = "en" 