# Deployment strategy

This is an implementation direction, not a claim that deployment exists. Develop with Docker Compose or equivalent only after tooling decisions; exact image versions and hosting are open.

## Environments and configuration

- Keep development, test, staging, and production data/config separate.
- Inject secrets through environment/secret manager, never source control. Validate required configuration at startup without printing values.
- Use private PostgreSQL/Redis networks; expose only TLS-protected web entrypoint. Restrict worker access to media storage and required model artifacts.
- Phase 2 provides a development-only Compose stack for React/Vite, Django, Celery, PostgreSQL, Redis, and the CV package liveness process. It is not production deployment. Phase 14 hardens/reviews image builds and CI artifacts; do not bundle unneeded CCTV credentials or model training tools.

## Release and operations

CI should run lint/type checks, unit/integration/API/frontend tests, migrations checks, dependency/security checks, and image build. Deployment should use reviewed migrations, health/readiness checks, rollback plan, and staged release. Worker/media compatibility must be maintained across rollout. Monitor request/job latency, queue depth, failure/retry rates, disk capacity, storage integrity, and sanitized resource health; avoid logging raw video or secrets.

Define database and media backup/restore as a coordinated plan, test restore before production, and define retention/deletion, incident response, data residency, encryption, SLOs, and recovery objectives with stakeholders. CCTV/VMS network access and any firewall/VPN/network-share arrangement are future, institution-specific decisions. Actual college integration is Phase 16 only.
