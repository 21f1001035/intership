from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FileStorageService(ABC):
    """Abstract base class for file storage backends."""

    @abstractmethod
    def save_file(self, file_bytes: bytes, filename: str, subfolder: str) -> str:
        """
        Persist file_bytes under subfolder/filename.

        Returns:
            storage_key — the relative path used to retrieve the file later.
        """

    @abstractmethod
    def get_file(self, storage_key: str) -> bytes:
        """
        Retrieve the raw bytes of a previously stored file.

        Raises:
            FileNotFoundError if the storage_key does not exist.
        """

    @abstractmethod
    def delete_file(self, storage_key: str) -> None:
        """
        Delete the file identified by storage_key.

        Raises:
            FileNotFoundError if the storage_key does not exist.
        """

    @staticmethod
    def compute_checksum(file_bytes: bytes) -> str:
        """Return the SHA-256 hex digest of the given bytes."""
        return hashlib.sha256(file_bytes).hexdigest()


class LocalFileStorage(FileStorageService):
    """
    Stores files on the local filesystem under LOCAL_STORAGE_PATH.

    storage_key format: "<subfolder>/<filename>"
    """

    def __init__(self, base_path: str | None = None) -> None:
        self._base = Path(base_path or settings.LOCAL_STORAGE_PATH).resolve()
        self._base.mkdir(parents=True, exist_ok=True)
        logger.info("LocalFileStorage initialised", base_path=str(self._base))

    def save_file(self, file_bytes: bytes, filename: str, subfolder: str) -> str:
        """Save file_bytes to <base>/<subfolder>/<filename>, creating dirs as needed."""
        # Sanitise the filename to avoid path traversal
        safe_filename = Path(filename).name
        target_dir = self._base / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / safe_filename
        # If a file with the same name already exists, append a counter
        counter = 1
        stem = Path(safe_filename).stem
        suffix = Path(safe_filename).suffix
        while target_path.exists():
            target_path = target_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        target_path.write_bytes(file_bytes)
        storage_key = f"{subfolder}/{target_path.name}"
        logger.info(
            "File saved",
            storage_key=storage_key,
            size_bytes=len(file_bytes),
        )
        return storage_key

    def get_file(self, storage_key: str) -> bytes:
        """Read and return the bytes of the file identified by storage_key."""
        file_path = self._base / storage_key
        if not file_path.exists():
            raise FileNotFoundError(
                f"File not found in local storage: {storage_key}"
            )
        return file_path.read_bytes()

    def delete_file(self, storage_key: str) -> None:
        """Delete the file identified by storage_key."""
        file_path = self._base / storage_key
        if not file_path.exists():
            raise FileNotFoundError(
                f"File not found in local storage: {storage_key}"
            )
        file_path.unlink()
        logger.info("File deleted", storage_key=storage_key)


def get_storage_service() -> FileStorageService:
    """
    Factory function returning the configured storage backend.
    Extend this to return S3 / DigitalOcean Spaces by checking settings.STORAGE_BACKEND.
    """
    if settings.STORAGE_BACKEND == "local":
        return LocalFileStorage()
    # Future: add "s3" / "digitalocean" branches here
    raise ValueError(f"Unsupported STORAGE_BACKEND: {settings.STORAGE_BACKEND!r}")
