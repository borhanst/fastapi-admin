"""File storage backends."""

from fastapi_console.storage.base import StorageBackend
from fastapi_console.storage.local import LocalStorageBackend

__all__ = ["StorageBackend", "LocalStorageBackend"]
