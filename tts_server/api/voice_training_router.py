"""Voice training API router for voice cloning operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from tts_server.api.response_models import (
    DeleteVoiceResponse,
    VoiceListResponse,
    VoiceResponse,
)
from tts_server.core.di import get_container
from tts_server.services.clone_speech import CloneSpeechService

router = APIRouter(prefix="/voices", tags=["Voice Cloning"])


def get_clone_service() -> CloneSpeechService:
    """Dependency to get clone service."""
    return get_container().clone_service


@router.post(
    "/clone",
    summary="Clone a voice from audio samples",
    description="Create a new voice model from audio samples.",
    response_model=VoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def clone_voice(
    name: Annotated[str, Form(description="Name for the cloned voice")],
    audio_files: Annotated[
        list[UploadFile],
        File(description="Audio sample files for voice cloning"),
    ],
    service: Annotated[CloneSpeechService, Depends(get_clone_service)],
    description: Annotated[str, Form()] = "",
    language: Annotated[str, Form()] = "en",
) -> VoiceResponse:
    """Clone a voice from uploaded audio samples."""
    if not audio_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one audio file is required",
        )
    
    # Read audio files into bytes
    audio_samples = []
    for file in audio_files:
        content = await file.read()
        audio_samples.append(content)
    
    voice = await service.clone_voice(
        name=name,
        audio_samples=audio_samples,
        description=description,
        language=language,
    )
    
    return VoiceResponse(
        id=voice.id,
        name=voice.name,
        description=voice.description,
        language=voice.language,
        created_at=voice.created_at,
        metadata=voice.metadata,
    )


@router.get(
    "",
    summary="List all cloned voices",
    response_model=VoiceListResponse,
)
async def list_voices(
    service: Annotated[CloneSpeechService, Depends(get_clone_service)],
) -> VoiceListResponse:
    """Get all stored cloned voices."""
    voices = await service.list_voices()
    return VoiceListResponse(
        voices=[
            VoiceResponse(
                id=v.id,
                name=v.name,
                description=v.description,
                language=v.language,
                created_at=v.created_at,
                metadata=v.metadata,
            )
            for v in voices
        ],
        count=len(voices),
    )


@router.get(
    "/{voice_id}",
    summary="Get a specific voice",
    response_model=VoiceResponse,
)
async def get_voice(
    voice_id: UUID,
    service: Annotated[CloneSpeechService, Depends(get_clone_service)],
) -> VoiceResponse:
    """Get a specific cloned voice by ID."""
    voice = await service.get_voice(voice_id)
    if voice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voice with ID {voice_id} not found",
        )
    
    return VoiceResponse(
        id=voice.id,
        name=voice.name,
        description=voice.description,
        language=voice.language,
        created_at=voice.created_at,
        metadata=voice.metadata,
    )


@router.delete(
    "/{voice_id}",
    summary="Delete a cloned voice",
    response_model=DeleteVoiceResponse,
)
async def delete_voice(
    voice_id: UUID,
    service: Annotated[CloneSpeechService, Depends(get_clone_service)],
) -> DeleteVoiceResponse:
    """Delete a cloned voice by ID."""
    deleted = await service.delete_voice(voice_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voice with ID {voice_id} not found",
        )
    
    return DeleteVoiceResponse(
        success=True,
        message=f"Voice {voice_id} deleted successfully",
    )