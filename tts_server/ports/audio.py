from abc import abstractmethod
from typing import Protocol

from tts_server.domain.models import PlaybackRequest, PlaybackStatus


class AudioPlaybackPort(Protocol):

    @abstractmethod
    async def play(self, request: PlaybackRequest) -> PlaybackStatus:
        """Play audio through system speakers.
        
        Blocks until playback completes.
        
        Args:
            request: Playback request with audio data and parameters
            
        Returns:
            Playback status after completion
        """
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop any current playback immediately."""
        ...

    @abstractmethod
    def is_playing(self) -> bool:
        """Check if audio is currently playing.
        
        Returns:
            True if playback is in progress, False otherwise
        """
        ...

    @abstractmethod
    async def play_file(self, file_path: str) -> PlaybackStatus:
        """Play a WAV file through system speakers.
        
        Blocks until playback completes.
        
        Args:
            file_path: Absolute path to WAV file
            
        Returns:
            Playback status after completion
            
        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file is not a valid WAV file
        """
        ...
