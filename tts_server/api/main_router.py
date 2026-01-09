import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from tts_server.core.di import get_container
from tts_server.domain.models import SynthPlayState

logger = logging.getLogger(__name__)

router = APIRouter()


class SynthPlayWSRequest(BaseModel):
    """WebSocket request model for synthesize + playback."""

    text: str
    voice_id: UUID | None = None
    language: str = "en"


class SynthPlayWSMessage(BaseModel):
    """WebSocket message model for state updates."""

    state: str
    message: str | None = None
    duration_seconds: float | None = None
    error: str | None = None


@router.websocket("/ws/synth-play")
async def synth_play_websocket(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for synthesize + playback.

    Flow:
    1. Client connects
    2. Client sends JSON: {"text": "...", "voice_id": null, "language": "en"}
    3. Server sends state updates: {"state": "synthesizing", "message": "..."}
    4. Server sends state updates: {"state": "playing", "message": "..."}
    5. Server sends final: {"state": "completed", "duration_seconds": 1.5}
    6. Connection closes

    On error:
    - Server sends: {"state": "error", "error": "..."}
    - Connection closes
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted for synth-play")

    try:
        # Receive request
        data = await websocket.receive_json()
        request = SynthPlayWSRequest.model_validate(data)
        logger.info(f"Received synth-play request: {request.text[:50]}...")

        container = get_container()
        service = container.synth_play_service

        # Resolve voice if provided
        voice = None
        if request.voice_id:
            voice = await container.voice_repository.get(request.voice_id)

        async def on_state_change(state: SynthPlayState, message: str | None) -> None:
            """Send state update to WebSocket client."""
            ws_message = SynthPlayWSMessage(
                state=state.value,
                message=message,
            )
            await websocket.send_json(ws_message.model_dump(exclude_none=True))

        # Execute synthesize + play
        status = await service.synthesize_and_play(
            text=request.text,
            voice=voice,
            language=request.language,
            on_state_change=on_state_change,
        )

        # Send final completed message with duration
        final_message = SynthPlayWSMessage(
            state=SynthPlayState.COMPLETED.value,
            message="Playback complete",
            duration_seconds=status.duration_seconds,
        )
        await websocket.send_json(final_message.model_dump(exclude_none=True))

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.exception("Error in synth-play WebSocket")
        error_message = SynthPlayWSMessage(
            state=SynthPlayState.ERROR.value,
            error=str(e),
        )
        try:
            await websocket.send_json(error_message.model_dump(exclude_none=True))
        except Exception:
            pass  # Client may have disconnected
    finally:
        try:
            await websocket.close()
        except Exception:
            pass  # Already closed
