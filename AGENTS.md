# Project-X Engineering Rules

These rules apply to every future Codex session and contributor. The product name is undecided; use **Project-X** or **Classroom Engagement Analytics** as a temporary working name. Do not invent a final name.

## Architecture rules
- Build a modular Django/DRF monolith for application workflows. Keep the Python CV engine behind a versioned, structured interface; it may initially run as a separately packaged worker/layer and is not a mandate to deploy many services.
- Preserve explicit boundaries between identity/access, institution/classroom/camera, academic scheduling, footage lifecycle/storage, processing orchestration, CV observation extraction, analytics, reporting/recommendations, and presentation.
- Use dependency inversion for storage and footage source adapters. Local video files are the MVP; future object storage and institution CCTV/VMS integrations must not require changes to downstream analytics contracts.
- Use asynchronous jobs for long-running media work. Django views must not execute CV processing.
- No business rules in React components. No CV implementation in Django views or serializers.

## Folder responsibilities
- `docs/`: approved product, requirements, architecture, data, API, AI, workflow, testing, and deployment specifications.
- `backend/` (future): Django apps and application/domain services; each app owns its migrations and tests.
- `frontend/` (future): React pages, feature modules, shared UI, and API client.
- `ai/`: independent Python package and future processing runtime; it must not import Django application code.
- `docker-compose.yml`: development-only multi-container wiring; production deployment belongs to a later phase.
- `.github/workflows/`: continuous integration checks; no deployment workflow until explicitly designed.
- Do not add business models, CRUD, or actual inference as part of repository/tooling foundation.

## Backend rules
- Django + Django REST Framework; PostgreSQL is the authoritative application metadata database.
- Keep business logic in testable services/use cases. Views coordinate HTTP; serializers validate transport input; model methods remain small and local.
- Use explicit transactions for multi-entity lifecycle changes. Use migrations for every schema change; never edit production schema manually.
- Keep same-row invariants in database constraints. Django does not call `full_clean()` on `save()`, so application use cases must run model validation before writes that depend on cross-entity rules.
- Keep development, test, and production settings separated; production settings must fail closed when secrets/hosts are missing.
- Long work is dispatched through Celery/Redis with idempotency, bounded retries, and persisted status/error metadata.
- Expose versioned REST endpoints under `/api/v1/`. Use stable identifiers, pagination for collections, consistent error envelopes, and UTC ISO-8601 timestamps.

## Frontend rules
- React pages compose feature components; API access belongs in a typed/service client layer, and domain rules stay server-side.
- Centralize authentication/session handling, route guards, permission-aware controls, request cancellation, and error mapping.
- Every data view handles loading, empty, success, and recoverable error states. Never treat hidden UI controls as authorization.
- Follow accessible semantic HTML, keyboard operation, and responsive layouts.
- Keep frontend package versions pinned and commit `package-lock.json`; use `npm ci` in automation.

## AI/CV isolation rules
- CV accepts an authorized video reference plus processing configuration and returns versioned structured observations. It does not write application entities or make teacher recommendations.
- Keep observable signals distinct from inferred constructs. Never claim to measure emotion, boredom, interest, intelligence, motivation, or psychological/mental state.
- Analytics owns documented aggregation rules and confidence/coverage handling. Recommendations are deterministic rules over validated analytics; an optional future LLM may phrase approved findings but may not invent metrics or evidence.
- Record model/pipeline/config versions, sampling policy, failures, and quality measures. Do not train models without an approved dataset, consent/privacy review, and evaluation plan.

## Database and storage rules
- Store video bytes in local/file storage for MVP, never in PostgreSQL. PostgreSQL stores metadata, storage keys/references, checksums, lifecycle state, observations, and analytics.
- Access media through a storage interface; persist provider and opaque object key, not assumptions tied to a machine path. Resolve paths only inside the adapter and enforce allowed roots.
- Use UUID primary keys, foreign keys, deliberate uniqueness/index constraints, audit timestamps, and soft deletion only where lifecycle/audit needs justify it.
- Do not store unnecessary identifiable student data. Prefer pseudonymous track identifiers scoped to one footage processing run; do not create student identity profiles in MVP.

## API, auth, and security
- Authentication is global. Initial roles are `ADMIN` and `TEACHER`; enforce object-level institution/classroom/lecture access on the server for every request.
- Hash passwords with Django's supported password hashers; never log passwords, tokens, raw frames, or secrets. Use HTTPS in deployment, secure cookies if session auth is selected, CSRF protection where applicable, and rate limiting on authentication.
- Validate MIME/container and media limits using content inspection, not client claims alone. Defend against path traversal, unsafe archive/media parsing, injection, and unauthorized file access.
- Use least privilege, environment-based configuration, secret management, audit sensitive actions, and define retention/deletion behavior before production data is used.

## Testing and feature completion
- Each feature requires unit, integration/API, authorization, validation, error-path, and relevant frontend/CV tests. Add end-to-end tests for the documented critical journey.
- A feature/module is complete only when implementation, database integration, API, validation, authorization, tests, documentation, error handling, and dependent-module integration all work.
- Maintain a small, approved, de-identified validation dataset; test deterministic contracts and quality/coverage, not only that models execute.
- Do not add or run tests unless requested for the current task; this rule governs future feature work.

## Git and change practices
- Do not break existing functionality. Inspect current status and local changes before editing; preserve unrelated user changes.
- Use a focused branch per change, descriptive commits, and reviewable vertical slices. Do not force-push, rewrite shared history, or commit secrets/data.
- Avoid unrelated formatting, generated artifacts, and dependency changes. Do not add dependencies before the relevant roadmap phase.

## Documentation and decisions
- Every feature needs acceptance criteria and updated API/data/workflow docs when contracts change.
- Record consequential choices and alternatives in `docs/architecture/architecture-decisions.md`; mark unresolved choices as open rather than silently assuming.
- Diagrams must match the written responsibilities, entities, statuses, and interfaces. Update all affected diagrams when a contract changes.
- Do not claim the system is implemented when it is still planned. Mark future integration and unverified deployment decisions clearly.
