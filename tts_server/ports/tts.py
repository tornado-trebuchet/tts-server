"""Port (interface) for TTS adapters."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from tts_server.domain.models import CloneRequest, TTSRequest, TTSResponse, VoiceModel


class TTSPort(ABC):
    """Abstract base class defining TTS adapter interface.
    
    All TTS adapters (Coqui, Tortoise, Bark, etc.) must inherit from this class.
    """

    @abstractmethod
    async def synthesize(self, request: TTSRequest, voice: VoiceModel | None = None) -> TTSResponse:
        """Synthesize speech from text.
        
        Args:
            request: TTS request with text and parameters
            voice: Optional voice model to use (None = default voice)
            
        Returns:
            Complete audio response with metadata
        """
        ...

    @abstractmethod
    def synthesize_stream(
        self, request: TTSRequest, voice: VoiceModel | None = None
    ) -> AsyncIterator[bytes]:
        """Stream synthesized speech chunks.
        
        Args:
            request: TTS request with text and parameters
            voice: Optional voice model to use (None = default voice)
            
        Yields:
            Audio data chunks as bytes
        """
        ...

    @abstractmethod
    async def clone_voice(self, request: CloneRequest) -> VoiceModel:
        """Create a cloned voice from audio samples.
        
        Args:
            request: Clone request with audio samples and metadata
            
        Returns:
            Created voice model (without persistence - that's repository's job)
        """
        ...

    @abstractmethod
    async def get_available_voices(self) -> list[str]:
        """Get list of built-in voice names available in this adapter.
        
        Returns:
            List of voice identifiers
        """
        ...

    @abstractmethod
    async def get_supported_languages(self) -> list[str]:
        """Get list of supported language codes.
        
        Returns:
            List of language codes (e.g., ['en', 'es', 'fr'])
        """
        ...