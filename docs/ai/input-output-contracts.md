# CV input/output contracts

Contract is conceptual and versioned (`cv-observations/v1`). The worker streams media via the storage adapter; it does not pass local absolute paths to remote/untrusted code.

## Input

```json
{
  "contract": "cv-processing-request/v1",
  "job_id": "uuid",
  "footage_id": "uuid",
  "media": {"provider": "local", "key": "opaque-storage-key", "checksum_sha256": "hex"},
  "recorded_start": "2026-01-01T09:00:00Z",
  "recorded_end": "2026-01-01T10:00:00Z",
  "sampling": {"policy_version": "sample-v1", "target_fps": 1.0},
  "pipeline": {"version": "pipeline-version", "options": {}}
}
```

Input constraints: authorized asset reference, matching checksum, finite time interval, supported media, bounded duration/resolution/size, and allow-listed sampling/configuration. Numeric policies are deployment config and remain open.

## Output

```json
{
  "contract": "cv-observations/v1",
  "job_id": "uuid",
  "pipeline_version": "pipeline-version",
  "model_versions": {"detector": "version", "tracker": "version", "landmarks": "version"},
  "media_info": {"duration_ms": 3600000, "width": 1920, "height": 1080},
  "coverage": {"sampled_frames": 3600, "decode_failures": 0, "observable_windows": 1200, "policy": "sample-v1"},
  "observations": [{
    "window_start_ms": 0,
    "window_end_ms": 3000,
    "track_ref": "run-scoped-pseudonym",
    "face_visible": {"value": true, "confidence": 0.91},
    "head_orientation": {"yaw_deg": 8.2, "pitch_deg": 2.1, "confidence": 0.76},
    "eye_state": {"state": "open", "confidence": 0.72},
    "quality_flags": []
  }],
  "warnings": []
}
```

All observation fields may be unknown/null with explicit reason/quality flags. Allowed eye states are `open`, `closed`, `unknown`; never infer a mental state. Confidence is model confidence, not probability of interest or truth. Output contains no face image, identity, or cross-run track key.

## Failure contract

Return typed safe error codes such as `MEDIA_UNREADABLE`, `UNSUPPORTED_MEDIA`, `RESOURCE_LIMIT`, `MODEL_UNAVAILABLE`, `INFERENCE_TIMEOUT`, `OUTPUT_SCHEMA_INVALID`, `INSUFFICIENT_COVERAGE`, plus a correlation ID and redacted diagnostics. No partial result is marked complete unless the selected policy explicitly accepts partial coverage and marks it. Retries are limited to transient failures, not invalid media or invalid schema.
