"""File storage backends."""

from fastapi_admin.storage.base import StorageBackend
from fastapi_admin.storage.local import LocalStorageBackend

__all__ = ["StorageBackend", "LocalStorageBackend"]
