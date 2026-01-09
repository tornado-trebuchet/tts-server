from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from tts_server.domain.models import VoiceModel


class VoiceRepositoryPort(Protocol):

    @abstractmethod
    async def save(self, voice: VoiceModel, voice_data: bytes) -> VoiceModel:
        """Save a voice model with its data.
        
        Args:
            voice: Voice model metadata
            voice_data: Raw voice embedding/model data
            
        Returns:
            Saved voice model with updated file_path
        """
        ...

    @abstractmethod
    async def get(self, voice_id: UUID) -> VoiceModel | None:
        """Retrieve a voice model by ID.
        
        Args:
            voice_id: UUID of the voice model
            
        Returns:
            Voice model if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_voice_data(self, voice_id: UUID) -> bytes | None:
        """Retrieve raw voice data by ID.
        
        Args:
            voice_id: UUID of the voice model
            
        Returns:
            Raw voice data bytes if found, None otherwise
        """
        ...

    @abstractmethod
    async def list_all(self) -> list[VoiceModel]:
        """List all stored voice models.
        
        Returns:
            List of all voice models (metadata only, not data)
        """
        ...

    @abstractmethod
    async def delete(self, voice_id: UUID) -> bool:
        """Delete a voice model.
        
        Args:
            voice_id: UUID of the voice model to delete
            
        Returns:
            True if deleted, False if not found
        """
        ...

    @abstractmethod
    async def exists(self, voice_id: UUID) -> bool:
        """Check if a voice model exists.
        
        Args:
            voice_id: UUID of the voice model
            
        Returns:
            True if exists, False otherwise
        """
        ...