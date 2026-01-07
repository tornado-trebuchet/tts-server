from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
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
    voice_id: UUID | None = None
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
    file_path: str | None = None 
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CloneRequest:
    """Request for voice cloning from audio samples."""
    name: str
    audio_samples: list[bytes]
    description: str = ""
    language: str = "en" 


@dataclass
class PlaybackRequest:
    """Request for audio playback on host device."""
    audio_data: bytes
    sample_rate: int
    channels: int = 1


@dataclass
class PlaybackStatus:
    """Status of audio playback."""
    is_playing: bool
    duration_seconds: float | None = None
