"""Audio API router for audio playback on host device."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from tts_server.api.response_models import (
    PlayAudioRequest,
    PlaybackStatusResponse,
    PlayFileRequest,
)
from tts_server.core.di import get_container
from tts_server.services.audio_playback import AudioPlaybackService

router = APIRouter(prefix="/audio", tags=["Audio Playback"])


def get_audio_service() -> AudioPlaybackService:
    """Dependency to get audio playback service."""
    return get_container().audio_service


@router.post(
    "/play-bytes",
    summary="Play raw audio bytes on host device",
    description="Play raw audio bytes (16-bit PCM) through system speakers. Blocks until playback completes.",
    response_model=PlaybackStatusResponse,
    responses={
        200: {
            "description": "Playback completed successfully",
        }
    },
)
async def play_audio_bytes(
    request: PlayAudioRequest,
    service: Annotated[AudioPlaybackService, Depends(get_audio_service)],
) -> PlaybackStatusResponse:
    """Play raw audio bytes through system speakers."""
    status_result = await service.play(
        audio_data=request.audio_data,
        sample_rate=request.sample_rate,
        channels=request.channels,
    )
    
    return PlaybackStatusResponse(
        is_playing=status_result.is_playing,
        duration_seconds=status_result.duration_seconds,
    )


@router.post(
    "/play-file",
    summary="Play a WAV file on host device",
    description="Play a WAV file through system speakers. Blocks until playback completes.",
    response_model=PlaybackStatusResponse,
    responses={
        200: {
            "description": "Playback completed successfully",
        },
        400: {
            "description": "Invalid file path or not a WAV file",
        },
        404: {
            "description": "File not found",
        },
    },
)
async def play_audio_file(
    request: PlayFileRequest,
    service: Annotated[AudioPlaybackService, Depends(get_audio_service)],
) -> PlaybackStatusResponse:
    """Play a WAV file through system speakers."""
    try:
        status_result = await service.play_file(file_path=request.file_path)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    
    return PlaybackStatusResponse(
        is_playing=status_result.is_playing,
        duration_seconds=status_result.duration_seconds,
    )


@router.post(
    "/stop",
    summary="Stop audio playback",
    description="Stop any currently playing audio immediately.",
    response_model=PlaybackStatusResponse,
)
async def stop_audio(
    service: Annotated[AudioPlaybackService, Depends(get_audio_service)],
) -> PlaybackStatusResponse:
    """Stop current playback."""
    await service.stop()
    
    return PlaybackStatusResponse(
        is_playing=False,
        duration_seconds=None,
    )


@router.get(
    "/status",
    summary="Get playback status",
    description="Check if audio is currently playing.",
    response_model=PlaybackStatusResponse,
)
async def get_status(
    service: Annotated[AudioPlaybackService, Depends(get_audio_service)],
) -> PlaybackStatusResponse:
    """Get current playback status."""
    return PlaybackStatusResponse(
        is_playing=service.is_playing(),
        duration_seconds=None,
    )
