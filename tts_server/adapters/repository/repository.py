import asyncio
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from tts_server.domain.models import VoiceModel
from tts_server.ports.repository import VoiceRepositoryPort


class FileVoiceRepository(VoiceRepositoryPort):
    def __init__(
        self,
        voices_dir: Path | str,
        metadata_file: str,
        voice_extension: str,
    ) -> None:

        self.voices_dir = Path(voices_dir).expanduser().resolve()
        self.voices_dir.mkdir(parents=True, exist_ok=True)

        self._metadata_file = metadata_file
        self._voice_extension = voice_extension

        self._metadata_path = self.voices_dir / self._metadata_file
        self._ensure_metadata_exists()

    def _ensure_metadata_exists(self) -> None:
        if not self._metadata_path.exists():
            self._write_metadata({})

    def _read_metadata(self) -> dict[str, Any]:
        with open(self._metadata_path) as f:
            return cast(dict[str, Any], json.load(f))

    def _write_metadata(self, metadata: dict[str, Any]) -> None:
        with open(self._metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

    def _voice_file_path(self, voice_id: UUID) -> Path:
        return self.voices_dir / f"{voice_id}{self._voice_extension}"

    def _voice_to_dict(self, voice: VoiceModel) -> dict[str, Any]:
        data = asdict(voice)
        data["id"] = str(voice.id)
        data["created_at"] = voice.created_at.isoformat()
        return data

    def _dict_to_voice(self, data: dict[str, Any]) -> VoiceModel:
        return VoiceModel(
            id=UUID(data["id"]),
            name=data["name"],
            description=data["description"],
            language=data["language"],
            created_at=datetime.fromisoformat(data["created_at"]),
            file_path=data.get("file_path"),
            metadata=data.get("metadata", {}),
        )

    async def save(self, voice: VoiceModel, voice_data: bytes) -> VoiceModel:
        voice_id_str = str(voice.id)
        voice_file = self._voice_file_path(voice.id)
        
        # Update voice with file path
        voice.file_path = str(voice_file)
        
        # Write voice data file
        await asyncio.to_thread(voice_file.write_bytes, voice_data)
        
        # Update metadata index
        metadata = await asyncio.to_thread(self._read_metadata)
        metadata[voice_id_str] = self._voice_to_dict(voice)
        await asyncio.to_thread(self._write_metadata, metadata)
        
        return voice

    async def get(self, voice_id: UUID) -> VoiceModel | None:
        """Retrieve a voice model by ID."""
        metadata = await asyncio.to_thread(self._read_metadata)
        voice_data = metadata.get(str(voice_id))
        if voice_data is None:
            return None
        return self._dict_to_voice(voice_data)

    async def get_voice_data(self, voice_id: UUID) -> bytes | None:
        """Retrieve raw voice data by ID."""
        voice_file = self._voice_file_path(voice_id)
        if not voice_file.exists():
            return None
        return await asyncio.to_thread(voice_file.read_bytes)

    async def list_all(self) -> list[VoiceModel]:
        metadata = await asyncio.to_thread(self._read_metadata)
        return [self._dict_to_voice(v) for v in metadata.values()]

    async def delete(self, voice_id: UUID) -> bool:
        voice_id_str = str(voice_id)
        metadata = await asyncio.to_thread(self._read_metadata)
        
        if voice_id_str not in metadata:
            return False
        
        # Remove from metadata
        del metadata[voice_id_str]
        await asyncio.to_thread(self._write_metadata, metadata)
        
        # Remove voice file
        voice_file = self._voice_file_path(voice_id)
        if voice_file.exists():
            await asyncio.to_thread(voice_file.unlink)
        
        return True

    async def exists(self, voice_id: UUID) -> bool:
        metadata = await asyncio.to_thread(self._read_metadata)
        return str(voice_id) in metadata