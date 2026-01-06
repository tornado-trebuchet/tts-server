"""TTS Server entry point."""

import uvicorn

from tts_server.core.settings import get_settings


def main() -> None:
    """Run the TTS server with uvicorn."""
    settings = get_settings()
    
    uvicorn.run(
        "tts_server.api.app:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
    )


if __name__ == "__main__":
    main()
