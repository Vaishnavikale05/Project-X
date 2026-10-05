"""Normalized boundary for recorded footage sources."""

from dataclasses import dataclass
from typing import BinaryIO, Protocol


@dataclass(frozen=True)
class SourceAsset:
    source_id: str
    filename: str
    content_type: str | None
    size_bytes: int | None


class FootageSource(Protocol):
    """Resolve and stream an already-recorded asset from a configured source."""

    def describe(self, source_reference: str) -> SourceAsset: ...

    def open(self, source_reference: str) -> BinaryIO: ...


class LocalSampleVideoProvider(FootageSource, Protocol):
    """Contract for sample-file access; ingestion policy is outside this adapter."""


class CollegeCCTVProvider(FootageSource, Protocol):
    """Future approved source adapter; no protocol/vendor is assumed or implemented."""
