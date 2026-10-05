# Classroom Engagement Analytics – Project-X

> **Temporary working name:** Project-X / Classroom Engagement Analytics. The final product name has not been decided.

## Project overview

Project-X is planned as an offline, post-lecture analytics system for physical college classrooms. It ingests recorded lecture footage, processes it asynchronously, and presents aggregated indicators based on observable visual signals. It is not a real-time monitoring product and does not claim to measure emotions or psychological states.

## Current status

**Phases 3, 4, and 5 are complete.** The developer's Windows Docker validation reported all six Compose services healthy, all migrations applied, 55/55 PostgreSQL/Redis backend tests passing, and successful browser workflow, reload persistence, classroom lifecycle, and camera lifecycle checks. Codex did not independently operate that environment. See [project status](PROJECT_STATUS.md) for the evidence record. Phase 6 has not started.

## Architecture summary

- React teacher/admin dashboard
- Django + Django REST Framework modular monolith
- PostgreSQL for application metadata, lifecycle state, structured observations, and analytics
- Local/file storage for MVP video bytes; replaceable storage adapter
- Redis + Celery for asynchronous processing orchestration
- Separate Python CV processing layer using a versioned input/output contract
- Future CCTV/VMS access through a `FootageProvider`; no institution-specific integration is assumed or implemented now
- Development-only Docker Compose stack and CI checks; no production deployment configuration

## Technology direction

The Phase 2 foundation pins Python 3.12, Django 5.2 LTS, DRF 3.18, Celery 5.6, React 19, TypeScript 5.9, Vite 8, Node 22, and exact direct package versions with Python/npm lockfiles. The development Compose stack targets PostgreSQL 17.6 and Redis 7.4. CI runs backend, frontend, AI contract, and container build checks.

OpenCV, YOLO, a tracking implementation, and MediaPipe remain CV candidates; none is installed and no model processing exists. Production image versions, deployment topology, and measured model selection remain future decisions.

Phase 2/3 verification and Phase 4/5 implementation and validation results are tracked in [PROJECT_STATUS.md](PROJECT_STATUS.md). OpenAPI generation has zero schema errors and one non-blocking ambiguous `status` enum naming warning. Production deployment validation remains future work.

## Repository structure

```text
AGENTS.md
README.md
PROJECT_STATUS.md
DEVELOPMENT_ROADMAP.md
.env.example
docker-compose.yml             # development only
backend/                       # Django modular monolith and adapters
frontend/                      # React application shell and tooling
ai/                            # independent CV contract/package and liveness process
.github/workflows/             # CI checks and image build verification
docs/                          # blueprint, contracts, and developer setup
```

The backend contains domain models and migrations in modular Django apps. Phase 5 adds institution-scoped institution/classroom/camera APIs and application services. The frontend adds an API-backed infrastructure management UI. Scheduling, footage, AI/CV, analytics, reports, recommendations, and deployment workflows remain future work.

## Local development

See [Development environment](docs/development-environment.md) for setup, migrations, demo metadata, and Phase 5 infrastructure workflows. Institution/classroom/camera APIs and the React infrastructure UI are implemented. Phase 5 Compose/PostgreSQL and browser validation were reported complete from the developer's Windows environment; production deployment validation remains future work.

## Documentation

- [Product overview](docs/product/product-overview.md)
- [System architecture](docs/architecture/system-architecture.md)
- [Module architecture](docs/architecture/module-architecture.md)
- [Domain/data model](docs/database/data-model.md)
- [ERD and class diagram](docs/database/entity-relationships.md)
- [API contracts](docs/api/api-contracts.md)
- [AI/CV architecture](docs/ai/ai-cv-architecture.md)
- [Developer environment setup](docs/development-environment.md)
- [Development roadmap](DEVELOPMENT_ROADMAP.md)
- [Project status](PROJECT_STATUS.md)

## Important architectural decisions

1. Process recorded footage after a lecture; do not perform live monitoring.
2. Keep the main backend a modular monolith; isolate CV through contracts without prematurely multiplying deployable services.
3. Keep video bytes outside PostgreSQL. PostgreSQL contains references and metadata.
4. Distinguish CV observations from business analytics and deterministic recommendations.
5. Design provider interfaces for later CCTV/VMS and object-storage integration; defer actual integrations.
6. Do not identify students in MVP; use per-run pseudonymous tracks and classroom aggregates.

See [architecture decisions](docs/architecture/architecture-decisions.md) for rationale and open decisions. Phase 5 decisions include bootstrap-only institution provisioning, global case-insensitive camera codes, explicit child-first deactivation, and redacted transactional audit for infrastructure mutations.
