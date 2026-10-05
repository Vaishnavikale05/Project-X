"""Versioned structured CV contract aligned with docs/ai/input-output-contracts.md."""

from dataclasses import dataclass
from typing import Any

CONTRACT_VERSION = "cv-observations/v1"


@dataclass(frozen=True)
class ProcessingRequest:
    job_id: str
    footage_id: str
    storage_provider: str
    storage_key: str
    checksum_sha256: str
    recorded_start: str
    recorded_end: str
    sampling_policy_version: str
    target_fps: float
    pipeline_version: str


@dataclass(frozen=True)
class CVResult:
    job_id: str
    pipeline_version: str
    model_versions: dict[str, str]
    media_info: dict[str, int]
    coverage: dict[str, Any]
    observations: list[dict[str, Any]]
    warnings: list[str]
    contract: str = CONTRACT_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Produce JSON-compatible output after checking core contract invariants."""
        if self.contract != CONTRACT_VERSION:
            raise ValueError(f"Unsupported CV output contract: {self.contract}")
        for observation in self.observations:
            start = observation.get("window_start_ms")
            end = observation.get("window_end_ms")
            if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
                raise ValueError("Observation windows must be non-negative, increasing integers")
            track_ref = observation.get("track_ref")
            if track_ref is not None and not isinstance(track_ref, str):
                raise ValueError("track_ref must be a run-scoped string or null")
        return {
            "contract": self.contract,
            "job_id": self.job_id,
            "pipeline_version": self.pipeline_version,
            "model_versions": self.model_versions,
            "media_info": self.media_info,
            "coverage": self.coverage,
            "observations": self.observations,
            "warnings": self.warnings,
        }


def validate_result(payload: dict[str, Any]) -> CVResult:
    """Parse the transport shape and enforce minimum schema checks."""
    if payload.get("contract") != CONTRACT_VERSION:
        raise ValueError(f"contract must be {CONTRACT_VERSION}")
    required = (
        "job_id",
        "pipeline_version",
        "model_versions",
        "media_info",
        "coverage",
        "observations",
        "warnings",
    )
    missing = [field for field in required if field not in payload]
    if missing:
        raise ValueError(f"missing CV result fields: {', '.join(missing)}")
    result = CVResult(
        contract=payload["contract"],
        job_id=payload["job_id"],
        pipeline_version=payload["pipeline_version"],
        model_versions=payload["model_versions"],
        media_info=payload["media_info"],
        coverage=payload["coverage"],
        observations=payload["observations"],
        warnings=payload["warnings"],
    )
    result.to_dict()
    return result
