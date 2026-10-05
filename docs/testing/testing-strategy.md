# Testing strategy

Tests are required as implementation proceeds; this document defines scope only. Do not use real student footage in routine tests. Prefer synthetic media/fixtures and approved de-identified samples with controlled access.

## Test layers

- **Unit:** domain services, policy rules, state transitions, validators, analytics formulas, retry/backoff decisions, recommendation provenance.
- **Integration:** PostgreSQL constraints/migrations, storage adapter atomic writes/checksum/path traversal, Redis/Celery task handoff and idempotency, CV contract parser, multi-module transactions.
- **API:** auth, role/object scope, validation/error envelope, pagination, state conflict, media upload limits, idempotency replay, no storage path leakage.
- **AI/CV:** media preflight, frame timestamp mapping, detection/tracking/landmark wrappers, missingness/coverage, schema version compatibility, deterministic synthetic scenes, failure modes, resource/throughput benchmarks.
- **Frontend:** page/component tests for loading/empty/error/complete states, auth expiry, route UX, role-specific controls, keyboard accessibility, API error rendering.
- **End-to-end:** admin configures classroom/camera/timetable/lecture; ingests valid sample footage; job completes; analytics and report persist; assigned teacher reads completed lecture; unassigned teacher is denied.
- **Migration/security:** forward/backward migration safety in development; authorization boundary, upload abuse, path traversal, credential handling, log redaction, dependency checks.

## Validation dataset strategy

Acquire representative material only with institutional approval, documented lawful basis/notice, retention rules, and access controls. De-identify where practical, minimize frames, do not commit media, and use a manifest with provenance/permissions. Split by lecture/recording, not random adjacent frames. Annotate observable signals with a rubric and uncertainty labels; record inter-annotator agreement. Hold out camera setups/lectures where possible. Evaluate quality and coverage by lighting, angle, occlusion, distance, and other relevant conditions. Keep threshold selection separate from final holdout evaluation. Dataset remains a blocker for model selection and meaningful performance claims.

## Quality gates

Run the relevant tests for each vertical slice and full suite before release. No feature is complete without authorization/error tests and updated docs. Numeric coverage, accuracy, performance, and security gates require stakeholder approval; never hide low coverage to pass a target.
