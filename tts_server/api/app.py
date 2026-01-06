from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from tts_server.api.response_models import ErrorResponse, HealthResponse
from tts_server.api.tts_router import router as tts_router
from tts_server.api.voice_training_router import router as voice_router
from tts_server.core.di import get_container


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    get_container()
    # await container.tts_adapter.get_available_voices()
    yield


def create_app() -> FastAPI:

    app = FastAPI(
        title="TTS Server",
        description="Local text-to-speech server with voice cloning support",
        version="0.1.0",
        lifespan=lifespan,
        responses={
            500: {"model": ErrorResponse, "description": "Internal Server Error"},
        },
    )
    
    # Mount routers
    app.include_router(tts_router)
    app.include_router(voice_router)
    
    @app.get(
        "/health",
        tags=["Health"],
        response_model=HealthResponse,
        summary="Health check",
    )
    async def health_check() -> HealthResponse:
        """Check server health status."""
        return HealthResponse(status="healthy", version="0.1.0")
    
    return app


app = create_app()