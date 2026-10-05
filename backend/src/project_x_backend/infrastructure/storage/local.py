"""Local-file MVP storage adapter with opaque keys and root confinement."""

import hashlib
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

from django.conf import settings

from .protocol import StorageMetadata, StoredObject

_SUFFIX = re.compile(r"^\.[A-Za-z0-9]{1,10}$|^$")


class LocalFileStorage:
    provider = "local"

    def __init__(self, root: Path | None = None):
        self.root = Path(root or settings.MEDIA_ROOT).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        candidate = (self.root / key).resolve()
        if candidate == self.root or not candidate.is_relative_to(self.root):
            raise ValueError("Storage key escapes the configured root")
        return candidate

    def save(self, stream: BinaryIO, *, suffix: str = "") -> StoredObject:
        if not _SUFFIX.fullmatch(suffix):
            raise ValueError("Invalid storage suffix")
        key = f"{uuid.uuid4().hex}{suffix.lower()}"
        destination = self._path(key)
        temporary = self._path(f".{uuid.uuid4().hex}.tmp")
        digest = hashlib.sha256()
        size = 0
        try:
            with temporary.open("xb") as output:
                while chunk := stream.read(1024 * 1024):
                    output.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
                output.flush()
                os.fsync(output.fileno())
            temporary.replace(destination)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return StoredObject(self.provider, key, size, digest.hexdigest())

    def retrieve(self, key: str) -> BinaryIO:
        return self._path(key).open("rb")

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def delete(self, key: str) -> bool:
        path = self._path(key)
        if not path.is_file():
            return False
        path.unlink()
        return True

    def metadata(self, key: str) -> StorageMetadata:
        path = self._path(key)
        if not path.is_file():
            raise FileNotFoundError(key)
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        stat = path.stat()
        return StorageMetadata(
            size_bytes=stat.st_size,
            checksum_sha256=digest.hexdigest(),
            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
        )
