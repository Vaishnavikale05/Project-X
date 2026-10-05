"""Storage port types. Domain/application code must not depend on filesystem paths."""

from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO, Protocol


@dataclass(frozen=True)
class StoredObject:
    provider: str
    key: str
    size_bytes: int
    checksum_sha256: str


@dataclass(frozen=True)
class StorageMetadata:
    size_bytes: int
    checksum_sha256: str
    modified_at: datetime


class StorageProvider(Protocol):
    def save(self, stream: BinaryIO, *, suffix: str = "") -> StoredObject: ...

    def retrieve(self, key: str) -> BinaryIO: ...

    def exists(self, key: str) -> bool: ...

    def delete(self, key: str) -> bool: ...

    def metadata(self, key: str) -> StorageMetadata: ...
