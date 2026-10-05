"""Provider-neutral file storage contract and MVP implementation."""

from .local import LocalFileStorage
from .protocol import StorageMetadata, StorageProvider, StoredObject

__all__ = ["LocalFileStorage", "StorageMetadata", "StorageProvider", "StoredObject"]
