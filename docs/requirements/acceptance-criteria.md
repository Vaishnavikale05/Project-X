# Acceptance criteria

## Blueprint acceptance

- Product is explicitly post-lecture/offline; no diagram implies live analysis.
- PostgreSQL is described as metadata/application database; local storage holds video bytes.
- Storage and source-provider interfaces shield downstream processing.
- CV structured observations are distinct from analytics and recommendation policy.
- Role/object access, asynchronous lifecycle, failures/retries, and versioned API are documented.
- Entity names, keys, relations, statuses, and diagrams are consistent.
- All requested diagram types are present and agree with prose.
- No business application implementation is introduced.

## Functional feature acceptance (future implementation)

| Requirement | Acceptance criteria |
|---|---|
| FR-01 Authentication and access | Valid active user authenticates; invalid/expired credentials receive `401`; wrong role or out-of-scope object is denied; deactivated users cannot continue; credential material never appears in logs. |
| FR-02 Resource management | ADMIN can create/read/update institution-scoped classrooms, cameras, subjects, users and timetable resources; duplicate codes and invalid references are rejected; TEACHER cannot mutate configuration. |
| FR-03 Lecture context | A lecture references valid classroom, subject, teacher, and optional timetable occurrence in the same institution; invalid interval or assignment is rejected; assigned teacher can read it and unrelated teacher cannot. |
| FR-04 Footage ingestion | Supported authorized recorded media is validated and associated with a lecture/camera; corrupt, unsupported, oversized, or out-of-scope input is rejected with a safe error; repeated idempotency key does not create duplicate asset effects. |
| FR-05 Storage | Video bytes are present only in the configured external storage adapter; PostgreSQL contains provider/key/metadata/checksum; application code cannot escape the allowed local storage root; checksum mismatch is detected. |
| FR-06 Processing lifecycle | Job persists before queue dispatch; duplicate delivery does not duplicate outputs; statuses, attempts, safe error code, and logs are queryable; retry occurs only for eligible transient failure and stops at configured limit. |
| FR-07 CV output | CV returns schema-valid observations with version, time mapping, confidence/quality flags and coverage; identity fields are absent; invalid schema or unreadable media becomes a typed failure, not successful output. |
| FR-08 Analytics | Versioned analytics consume CV output, expose approved proxy indicators with coverage/confidence/limitations, and are reproducible for the same input/ruleset; insufficient coverage is explicit; no psychological-state claim is made. |
| FR-09 Teacher access | Assigned teacher can retrieve lecture status/results; unassigned teacher cannot retrieve the same object; no raw local path or unauthorized footage is exposed. |
| FR-10 Reports | Report references an exact ready AnalyticsRun and includes its version/caveats; repeated generation for the same inputs is idempotent or creates a clearly versioned snapshot. |
| FR-11 Recommendations | Each recommendation carries rule and analytics evidence references; unsupported evidence cannot produce a recommendation; no LLM or rule invents a metric. |
| FR-12 Audit/operations | Authorized admin can inspect sanitized job/service health; security-sensitive actions record actor, time, object, and request ID; secrets and raw frames are absent. |
| FR-13 Replaceable providers | Contract tests prove local and future test-double providers yield the same normalized input/reference shape; downstream processing and analytics depend only on the contract. |

## Critical product journey acceptance (future implementation)

Given an authorized admin, configured classroom/camera, timetable and lecture; when valid sample footage is ingested, then file bytes reside in local storage and PostgreSQL contains only metadata/reference; when a processing job runs, then lifecycle/errors/logs and versioned CV output are persisted; when analytics/report rules run, then the teacher assigned to that lecture can view the result with coverage and limitations, while an unrelated teacher is denied.

## Feature completion gate

Implementation, database integration, API, validation, authorization, tests, documentation, errors, and dependent-module integration all work. Details are in `../AGENTS.md`.
