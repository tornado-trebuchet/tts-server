"""Pydantic models for API request/response validation."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class AudioFormatEnum(str, Enum):
    """Supported audio output formats for API."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"


# ============================================================================
# TTS Request/Response Models
# ============================================================================


class SynthesizeRequest(BaseModel):
    """Request body for text-to-speech synthesis."""
    
    text: str = Field(
        ...,
        description="Text to synthesize into speech",
        min_length=1,
        max_length=10000,
    )
    voice_id: UUID | None = Field(
        default=None,
        description="UUID of cloned voice to use (None = default voice)",
    )
    language: str = Field(
        default="en",
        description="Language code for synthesis",
    )
    speed: float = Field(
        default=1.0,
        description="Speech speed multiplier",
        ge=0.5,
        le=2.0,
    )


class SynthesizeResponse(BaseModel):
    """Response metadata for synthesis (audio is in body)."""
    
    audio_format: AudioFormatEnum
    sample_rate: int
    duration_seconds: float


class VoicesResponse(BaseModel):
    """List of available built-in voices."""
    
    voices: list[str]


class LanguagesResponse(BaseModel):
    """List of supported languages."""
    
    languages: list[str]


# ============================================================================
# Voice Cloning Request/Response Models
# ============================================================================


class CloneVoiceRequest(BaseModel):
    """Request body for voice cloning (audio samples sent separately)."""
    
    name: str = Field(
        ...,
        description="Name for the cloned voice",
        min_length=1,
        max_length=100,
    )
    description: str = Field(
        default="",
        description="Description of the voice",
        max_length=500,
    )
    language: str = Field(
        default="en",
        description="Language code for the voice",
    )


class VoiceResponse(BaseModel):
    """Voice model response."""
    
    id: UUID
    name: str
    description: str
    language: str
    created_at: datetime
    metadata: dict = Field(default_factory=dict)


class VoiceListResponse(BaseModel):
    """List of stored voices."""
    
    voices: list[VoiceResponse]
    count: int


class DeleteVoiceResponse(BaseModel):
    """Response for voice deletion."""
    
    success: bool
    message: str


# ============================================================================
# Error Models
# ============================================================================


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str
    detail: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = "healthy"
    version: str = "0.1.0"