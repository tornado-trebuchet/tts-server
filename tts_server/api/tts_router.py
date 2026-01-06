"""TTS API router for text-to-speech synthesis."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response, StreamingResponse

from tts_server.api.response_models import (
    LanguagesResponse,
    SynthesizeRequest,
    VoicesResponse,
)
from tts_server.core.di import get_container
from tts_server.services.text_to_speech import TextToSpeechService

router = APIRouter(prefix="/tts", tags=["Text-to-Speech"])


def get_tts_service() -> TextToSpeechService:
    """Dependency to get TTS service."""
    return get_container().tts_service


@router.post(
    "/synthesize",
    summary="Synthesize speech from text",
    description="Generate audio from text using TTS. Returns WAV audio.",
    response_class=Response,
    responses={
        200: {
            "content": {"audio/wav": {"schema": {"type": "string", "format": "binary"}}},
            "description": "Synthesized audio file in WAV format",
        }
    },
)
async def synthesize(
    request: SynthesizeRequest,
    service: Annotated[TextToSpeechService, Depends(get_tts_service)],
) -> Response:
    """Synthesize speech and return complete audio."""
    response = await service.synthesize(
        text=request.text,
        voice_id=request.voice_id,
        language=request.language,
        speed=request.speed,
    )
    
    return Response(
        content=response.audio_data,
        media_type="audio/wav",
        headers={
            "X-Audio-Duration": str(response.duration_seconds),
            "X-Sample-Rate": str(response.sample_rate),
        },
    )


@router.post(
    "/synthesize/stream",
    summary="Stream synthesized speech",
    description="Generate audio from text with streaming response.",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"audio/wav": {"schema": {"type": "string", "format": "binary"}}},
            "description": "Streaming audio data in WAV format",
        }
    },
)
async def synthesize_stream(
    request: SynthesizeRequest,
    service: Annotated[TextToSpeechService, Depends(get_tts_service)],
) -> StreamingResponse:
    """Synthesize speech and stream audio chunks."""
    audio_stream = service.synthesize_stream(
        text=request.text,
        voice_id=request.voice_id,
        language=request.language,
        speed=request.speed,
    )
    
    return StreamingResponse(
        content=audio_stream,
        media_type="audio/wav",
    )


@router.get(
    "/voices",
    summary="List available built-in voices",
    response_model=VoicesResponse,
)
async def list_voices(
    service: Annotated[TextToSpeechService, Depends(get_tts_service)],
) -> VoicesResponse:
    """Get list of built-in voices available for synthesis."""
    voices = await service.get_available_voices()
    return VoicesResponse(voices=voices)


@router.get(
    "/languages",
    summary="List supported languages",
    response_model=LanguagesResponse,
)
async def list_languages(
    service: Annotated[TextToSpeechService, Depends(get_tts_service)],
) -> LanguagesResponse:
    """Get list of supported language codes."""
    languages = await service.get_supported_languages()
    return LanguagesResponse(languages=languages)