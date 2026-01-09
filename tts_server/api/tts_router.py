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
    description="Generate audio from text using TTS. Returns raw 16-bit PCM audio.",
    response_class=Response,
    responses={
        200: {
            "content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}},
            "description": "Synthesized audio as raw 16-bit PCM",
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
        media_type="application/octet-stream",
        headers={
            "X-Audio-Duration": str(response.duration_seconds),
            "X-Sample-Rate": str(response.sample_rate),
            "X-Channels": str(response.channels),
            "X-Audio-Format": "pcm_s16le",
        },
    )


@router.post(
    "/synthesize/stream",
    summary="Stream synthesized speech",
    description="Generate audio from text with streaming response. Returns raw 16-bit PCM audio chunks.",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}},
            "description": "Streaming raw 16-bit PCM audio data",
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
        media_type="application/octet-stream",
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