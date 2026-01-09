from abc import abstractmethod
from typing import Protocol

from tts_server.domain.models import CloneRequest, VoiceModel


class VoiceCloningPort(Protocol):
    
    @abstractmethod
    async def clone_voice(self, request: CloneRequest) -> VoiceModel:
        """Create a cloned voice from audio samples.
        
        Args:
            request: Clone request with audio samples and metadata
            
        Returns:
            Created voice model (without persistence - that's repository's job)
        """
        ...