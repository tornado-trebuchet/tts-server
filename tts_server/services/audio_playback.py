from pathlib import Path

from tts_server.domain.models import PlaybackRequest, PlaybackStatus
from tts_server.ports.audio import AudioPlaybackPort


class AudioPlaybackService:
    """Service for playing audio on the host device."""

    def __init__(self, audio_adapter: AudioPlaybackPort) -> None:
        self._audio = audio_adapter

    async def play(
        self,
        audio_data: bytes,
        sample_rate: int,
        channels: int = 1,
    ) -> PlaybackStatus:
        """Play audio through system speakers.
        
        Blocks until playback completes.
        
        Args:
            audio_data: Raw audio bytes (16-bit PCM)
            sample_rate: Sample rate in Hz
            channels: Number of audio channels
            
        Returns:
            Playback status after completion
        """
        request = PlaybackRequest(
            audio_data=audio_data,
            sample_rate=sample_rate,
            channels=channels,
        )
        return await self._audio.play(request)

    async def play_file(self, file_path: str) -> PlaybackStatus:
        """Play a WAV file through system speakers.
        
        Blocks until playback completes.
        
        Args:
            file_path: Absolute path to WAV file
            
        Returns:
            Playback status after completion
            
        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If path is not absolute or file is not a WAV file
        """
        path = Path(file_path)
        
        if not path.is_absolute():
            raise ValueError(f"File path must be absolute: {file_path}")
        
        if not path.exists():
            raise FileNotFoundError(f"WAV file not found: {file_path}")
        
        if not path.suffix.lower() == ".wav":
            raise ValueError(f"File must have .wav extension: {file_path}")
        
        return await self._audio.play_file(file_path)

    async def stop(self) -> None:
        """Stop any current playback immediately."""
        await self._audio.stop()

    def is_playing(self) -> bool:
        """Check if audio is currently playing.
        
        Returns:
            True if playback is in progress, False otherwise
        """
        return self._audio.is_playing()
