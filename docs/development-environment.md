# Development environment

This guide covers the Phase 3 domain foundation, Phase 4 authentication, and Phase 5 institution/classroom/camera infrastructure slice. Institution context and infrastructure endpoints plus API-backed React admin pages exist. Other business workflows remain future work. Supported baseline: Python 3.12, Node.js 22.12+ and npm 10+, Docker Engine/Desktop with Compose v2 for the full service stack.

## Choose a workflow

- **Local Python/Node + Compose dependencies:** install the backend and AI Python tools into separate virtual environments, install the frontend with `npm ci`, then run PostgreSQL/Redis using `docker compose up postgres redis`.
- **Full Compose:** configure `.env`, then use `docker compose up --build` to start PostgreSQL, Redis, Django, Celery, React/Vite, and the AI liveness service.

Docker Compose is not available in this Codex implementation environment. The developer has reported successful Windows Docker Compose validation for Phases 4 and 5. See [PROJECT_STATUS.md](../PROJECT_STATUS.md); do not treat Codex-local SQLite checks as container validation.

## Configure local environment

```powershell
Copy-Item .env.example .env
```

Edit `.env` and choose local-only `DJANGO_SECRET_KEY`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` values. Leave it untracked. The example file intentionally contains blank credential values. Compose injects the PostgreSQL/Redis service hostnames. If running Django directly on the host, use `POSTGRES_HOST=localhost` and `REDIS_HOST=localhost`.

Generate a development secret locally if needed:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Never use the development `.env` in a deployed environment.

## Backend

```powershell
py -3.12 -m venv .venv-backend
.\.venv-backend\Scripts\Activate.ps1
python -m pip install -r backend/requirements-dev.lock
$env:PYTHONPATH = "backend/src"
$env:DJANGO_SETTINGS_MODULE = "project_x_backend.config.settings.development"
python backend/manage.py check
python backend/manage.py migrate
python backend/manage.py runserver
```

For local sample metadata and authentication accounts, run `python backend/manage.py seed_demo` after migrations. The command refuses to run unless `DEBUG=True`, creates only obviously fake `.invalid` users and metadata, and never creates video files. Demo accounts are `admin@project-x-demo.invalid` (ADMIN) and `teacher@project-x-demo.invalid` (TEACHER). Their development-only default password is `ProjectX-Demo-Only-Change-Me!`; override it with `PROJECT_X_DEMO_PASSWORD` before seeding if desired. Do not reuse this value outside a disposable development database. The seed command is idempotent and does not reset passwords for existing users.

`JWT_SIGNING_KEY` is optional in local development and falls back to `DJANGO_SECRET_KEY`; configure a separate strong key for deployments. Production settings require an explicit JWT signing key. Never commit `.env` or reuse demo credentials outside development.

The fast test mode explicitly uses in-memory SQLite and locmem cache. Pytest selects it by default from `backend/pyproject.toml`; Django's fast test command selects it with `--settings`. It is intended for quick local unit/API feedback and does not prove PostgreSQL or Redis behavior. The Dockerfile copies the repository-level `backend/tests` package into the image. From `backend/`, run:

```powershell
Set-Location backend
python manage.py makemigrations --check --dry-run --settings=project_x_backend.config.settings.test
python manage.py test --settings=project_x_backend.config.settings.test --verbosity 2
python -m pytest
```

`python manage.py test` without `--settings` uses `manage.py`'s `development` default, which is PostgreSQL/Redis configured from environment variables. That is not the recommended integration-test entry point: use the explicit integration module below so the intent is visible and it cannot silently become SQLite.

### PostgreSQL + Redis integration-test mode

The dedicated `project_x_backend.config.settings.test_postgres` module inherits the test-only signing key/password-independent settings, but restores PostgreSQL connection values and the configured Redis cache from `base.py`. It checks the requested engine and required connection values at startup, and raises a settings error instead of falling back to SQLite. If PostgreSQL or Redis is unreachable, the Django test database setup or Redis integration tests fail.

From the repository root in PowerShell, start the development stack and wait for healthy PostgreSQL and Redis:

```powershell
docker compose up -d --build
docker compose ps
docker compose exec backend python manage.py seed_demo
docker compose exec -e DJANGO_SETTINGS_MODULE=project_x_backend.config.settings.test_postgres backend python manage.py test --verbosity 2
```

Django creates a separate disposable test database on the same PostgreSQL service using the configured `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT`; test migrations and test data are run there, then it is destroyed at the end. The Compose database role must be allowed to create test databases (the standard image's initial `POSTGRES_USER` has this permission). The seeded development database is not used as the test database. Do not point this mode at production or use `--keepdb` unless you explicitly want to retain the test database.

Two integration-only tests are skipped in fast SQLite mode and execute in `test_postgres` mode. They assert Django's live database vendor is PostgreSQL, write/read/delete a unique value through the configured Redis cache, and verify the login throttle returns `429` after the configured per-IP request limit. Redis cache configuration is `django.core.cache.backends.redis.RedisCache`, using `DJANGO_CACHE_URL` when set or the base URL `redis://<REDIS_HOST>:<REDIS_PORT>/2`; Celery uses separate Redis databases `/0` and `/1`. Login/refresh throttles use DRF `ScopedRateThrottle` at 10/min and 30/min respectively in the application. DRF snapshots `DEFAULT_THROTTLE_RATES` on `ScopedRateThrottle.THROTTLE_RATES` when the class is imported, so a later `override_settings(REST_FRAMEWORK=...)` alone does not change an already-imported class. The integration test temporarily patches that actual class rate map to 1/minute, asserts the Redis throttle key/history and same requester identity, then restores the original production rates.

The developer reports Phase 4 validated against PostgreSQL/Redis on the Windows Docker host: 39 backend tests passed, including the Redis-backed throttle test. Codex did not execute this command in Docker. To repeat the check, use the command above and record fresh results; fast SQLite-mode results are not PostgreSQL evidence.

In a second terminal, use the same virtual environment and configured environment variables to start the infrastructure-only Celery worker:

```powershell
$env:PYTHONPATH = "backend/src"
$env:DJANGO_SETTINGS_MODULE = "project_x_backend.config.settings.development"
python -m celery -A project_x_backend.config.celery_app worker --loglevel=INFO
```

Run backend checks/tests from `backend/`:

```powershell
python -m ruff check src tests
python -m ruff format --check src tests
python -m pytest
```

Tests use isolated in-memory SQLite and mock dependency probes where appropriate; normal development settings use PostgreSQL.

## Frontend

```powershell
Set-Location frontend
npm ci
npm run dev
```

Then run `npm run lint`, `npm run typecheck`, `npm test`, `npm run format:check`, `npm run build`, and `npm audit --audit-level=high`. Vite proxies `/api` to `http://localhost:8000` by default. Override the target with `VITE_DEV_API_TARGET` if the backend is elsewhere.

## AI/CV package

The AI package is intentionally independent and has no Django dependency:

```powershell
py -3.12 -m venv .venv-ai
.\.venv-ai\Scripts\Activate.ps1
python -m pip install -r ai/requirements-dev.lock
Set-Location ai
python -m pytest
python -m ruff check src tests
python -m ruff format --check src tests
```

The Compose AI process exposes only `/health`. CV stage protocols and the versioned data contract exist; no frame/model processing is configured.

To start its liveness process directly, set `PYTHONPATH=ai/src` and run `python -m project_x_ai.health_server` from the repository root.

## Compose services and smoke checks

After `.env` configuration:

```powershell
docker compose config
docker compose up --build
```

Endpoints: frontend `http://localhost:5173`, backend readiness `http://localhost:8000/api/v1/health`, OpenAPI `http://localhost:8000/api/v1/schema/`, API docs `http://localhost:8000/api/v1/docs/`, AI liveness `http://localhost:8010/health`. Authentication routes are `/api/v1/auth/csrf/`, `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/auth/logout`, and `/api/v1/auth/me`. Backend readiness reports PostgreSQL and Redis state. Worker health uses Celery's `inspect ping`. A successful Compose health status verifies services can reach their dependencies.

For the browser auth flow, use this manual smoke checklist on the developer's Windows Compose environment:

1. Start with `docker compose up -d --build`; check `docker compose ps` and wait until PostgreSQL, Redis, backend, frontend, Celery, and AI report healthy.
2. Open `http://localhost:5173`.
3. Log in with the development demo account `admin@project-x-demo.invalid` or `teacher@project-x-demo.invalid`, using the development-only password configured by `PROJECT_X_DEMO_PASSWORD` (default documented above). Do not use real college credentials.
4. Confirm the protected application shell appears and displays the demo user's name, email, and `ADMIN` or `TEACHER` role.
5. In browser Network tools, confirm `GET /api/v1/auth/me` succeeds with the access token and returns safe current-user fields only.
6. Choose **Sign out** and confirm the app returns to the login page.
7. Reload the frontend. Confirm session restoration does not succeed: refresh returns `401` after the refresh cookie was revoked/cleared and the login page remains visible. The access token issued before logout can remain valid until its five-minute expiry; logout revokes refresh credentials, not already-issued access JWTs.
8. Submit a wrong password and confirm login fails with a generic invalid-credentials message; no account-existence detail is shown.
9. Optionally repeat steps 3–7 with the other demo role and confirm the displayed role matches the account. The developer reports browser login reached the authenticated application shell. Codex did not operate the browser; backend tests separately cover authentication, refresh rotation/blacklisting, and role authorization.

The React client obtains a CSRF token before login/refresh/logout, holds the five-minute access JWT in memory, and relies on the HttpOnly refresh cookie to restore a session after reload. `/api/v1/auth/me` is protected by Bearer access authentication. These routes are not public registration or user-management APIs.

### Phase 5 infrastructure browser smoke test

Run this checklist in the developer Windows Docker environment after Phase 5 PostgreSQL/Compose tests. Use development-only seeded accounts, never real credentials.

1. Run `docker compose up -d --build`; wait for all six services to report healthy with `docker compose ps`.
2. Open `http://localhost:5173` and log in as the seeded ADMIN.
3. Open **Institution** and confirm current institution context is shown with no create-institution action.
4. Create a classroom with a unique room code and positive capacity. Confirm it appears in the list/details.
5. Open the classroom and register a camera with a unique code and `LOCAL_FILE` source. Confirm it appears in the filtered camera list.
6. Reload and verify both records still appear from the API/database.
7. Edit classroom and camera metadata, then deactivate the camera. Confirm updated values/status persist.
8. Attempt classroom deactivation while an active camera exists; confirm a clear conflict and unchanged classroom state. Deactivate the camera first and retry.
9. Confirm matching `AuditEvent` records exist and contain safe actor/action/resource/changed-field metadata only.
10. Log in as TEACHER; confirm infrastructure is read-only and direct mutation requests return `403`. Confirm another institution's object IDs do not disclose records.

The developer reports this browser journey passed in the Windows Docker environment: workflow, reload persistence, classroom lifecycle, and camera lifecycle. Codex did not independently operate that environment; see `PROJECT_STATUS.md` for the validation record.

Docker CLI/Compose is unavailable in the current implementation workspace. The developer reports Phase 4 validation and Phase 5 final validation from the Windows Docker environment; see `PROJECT_STATUS.md` for the corresponding evidence. Codex did not independently verify those runtime results. Its separate fast-mode run used SQLite; those results are not PostgreSQL evidence. For a repeatable check, use the PostgreSQL/Redis test mode and browser checklist above. Logout revokes refresh credentials; an access JWT already issued can remain valid for up to five minutes as described in [authentication](api/authentication.md).

## Tooling choices

- Backend and AI direct dependencies are maintained in separate requirements files; resolved runtime and development locks capture every installed Python package while preserving the independent package boundary.
- Frontend dependencies are exact-version pinned in `package.json`, with `package-lock.json` as the full npm resolution lock and `npm ci` as the reproducible install command.
- Ruff handles Python lint and formatting; pytest/pytest-django test Python; TypeScript strict mode provides frontend type checks; ESLint and Prettier check frontend source; Vitest and Testing Library exercise the React shell/API client.
- Django's environment-specific settings modules separate development, test, and production behavior. Secrets are supplied through environment configuration, never tracked.
- Production settings fail startup when the application secret, allowed hosts, required database/Redis configuration, or an explicit positive HSTS duration is missing. Configure proxy/TLS behavior for the actual deployment before release.

Tool versions are reviewed in Phase 2 and should be upgraded through deliberate dependency updates with CI checks.
