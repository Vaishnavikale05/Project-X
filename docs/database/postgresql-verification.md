# Phase 3 PostgreSQL and Docker close-out verification

**Result:** Complete, based on the Windows Docker Compose validation reported on 2026-10-04.  
**Evidence source:** User-provided PowerShell output and verification summary. This documentation update records that evidence; the current editing host did not independently rerun Docker commands.

## PostgreSQL and service validation

The reported Compose validation confirmed:

| Service | Reported status |
| --- | --- |
| PostgreSQL | Healthy |
| Redis | Healthy |
| Celery worker | Healthy |
| AI service | Healthy |
| Django backend | Healthy |
| React frontend | Healthy |

All existing migrations had already been applied. The user confirmed the domain schema was present in PostgreSQL and the domain test run discovered and passed all **24 backend tests** against PostgreSQL. The supplied summary did not include raw `docker compose ps`, test runner output, database identity, or detailed constraint/index query output; no engine/database name or individual constraint/index names are inferred here.

## Seed idempotency

`seed_demo` was run repeatedly in the Compose backend. The supplied count snapshots, taken immediately before and after an additional `call_command("seed_demo")`, were identical:

| Model | Before | After |
| --- | ---: | ---: |
| User | 2 | 2 |
| Institution | 1 | 1 |
| Classroom | 2 | 2 |
| Camera | 2 | 2 |
| TimetableEntry | 1 | 1 |
| Lecture | 2 | 2 |
| Footage | 1 | 1 |
| ProcessingJob | 0 | 0 |
| ProcessingLog | 0 | 0 |
| CVRun | 0 | 0 |
| CVObservation | 0 | 0 |
| AnalyticsRun | 0 | 0 |
| IndicatorAggregate | 0 | 0 |
| LectureSummary | 0 | 0 |
| LectureReport | 0 | 0 |
| Recommendation | 0 | 0 |
| AuditEvent | 0 | 0 |

All 17 model counts had a zero delta. The command also reported: “No video file was created or stored.” The transcript's final optional delta-print statement had `exit()` appended and raised a syntax error after both snapshots had printed; direct comparison of the complete before/after counts confirms no duplicates.

## Storage separation and scope

The reported Phase 3 PostgreSQL validation confirmed that video binaries are not stored in PostgreSQL. PostgreSQL holds domain metadata and storage references; video bytes remain outside the database in configured local/file storage. This page records Phase 3 verification only; Phase 4 authentication has since been completed and Phase 5 adds institution/classroom/camera APIs. Later ingestion, AI inference, analytics, reports, and recommendations remain unimplemented.

## Health-check and OpenAPI notes

The backend and frontend health-check configuration fixes are included in the Compose setup and both services were reported healthy in the Phase 3 Windows Docker run. The health endpoint serializer warning was fixed during Phase 4. Phase 5 schema generation currently has one non-blocking warning about disambiguating multiple `status` enum names; the schema generates with zero errors.

## Close-out

Phase 3 — Database & Domain Foundation is **complete** based on the reported PostgreSQL-backed migrations/schema, 24 passing PostgreSQL-backed tests, repeated seed counts, storage separation, and six healthy Compose services. This does not assert production deployment validation. Phase 4 and Phase 5 status is tracked in the current [project status](../../PROJECT_STATUS.md).
