"""Footage source adapter contracts. No institution CCTV integration exists yet."""

from .protocol import CollegeCCTVProvider, FootageSource, LocalSampleVideoProvider, SourceAsset

__all__ = ["CollegeCCTVProvider", "FootageSource", "LocalSampleVideoProvider", "SourceAsset"]
