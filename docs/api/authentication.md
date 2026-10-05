# Authentication architecture

Authentication is global under `/api/v1/auth`; authorization is checked on every protected request. The Phase 3 custom Django user remains the identity source of truth. Email lookup is case-insensitive, and only active accounts can obtain or refresh credentials. Public registration is not provided.

## Protocol and token policy

- Access credentials are JWTs signed with HS256. The access lifetime is **5 minutes**; the refresh lifetime is **12 hours**.
- Claims include `user_id`, `token_type`, `jti`, `iat`, and `exp`. Role and institution are deliberately read from the current user row on each authenticated request rather than trusted from token claims, so role changes and deactivation take effect immediately for new requests.
- `JWT_SIGNING_KEY` is injected from the environment. Development may use `DJANGO_SECRET_KEY` when no separate JWT key is configured. Production requires a distinct non-empty `JWT_SIGNING_KEY`; it is never committed.
- The access token is returned in JSON and kept only in React application memory. The refresh JWT is returned only as an HttpOnly, SameSite=Lax cookie scoped to `/api/v1/auth/`; JavaScript cannot read it. The cookie is Secure in production and non-Secure only for local HTTP development.
- Refresh rotates the refresh JWT and blacklists the preceding token. Rotation resets the 12-hour refresh expiry, so the session has a 12-hour inactivity limit but no separate absolute maximum while it is actively refreshed.
- Logout blacklists the refresh credential and clears its cookie. Previously issued access JWTs are not checked against a denylist and can remain usable until their maximum five-minute expiry. React drops the in-memory access token immediately.
- SimpleJWT's blacklist app persists outstanding/blacklisted refresh token records in PostgreSQL. Database access must be restricted; records contain signed bearer-token material and must be included in the database retention/security policy.
- React keeps the access JWT only in memory. If it remains open after logout, calls using that JWT may succeed until its `exp` (at most five minutes from issue); reload/session restoration fails because the refresh cookie is cleared and blacklisted.

This is a browser-oriented JWT design, not a security certification. Use HTTPS in production, protect the signing secret, maintain restrictive CSP/XSS defenses, and deploy the SPA and API same-origin (or deliberately configure CORS and CSRF for the chosen topology). No external identity provider is assumed.

## Authentication flow

1. `GET /api/v1/auth/csrf/` sets Django's HttpOnly CSRF cookie and returns a masked CSRF token in JSON.
2. The client sends that token in `X-CSRFToken` with the JSON login request. The server applies Django password hashing verification, case-insensitive identity lookup, active-account checks, and a shared Redis-backed IP rate limit.
3. Login returns an access JWT and safe user profile; the refresh token is set in the HttpOnly cookie. Failed credentials return the same generic `401` for unknown, wrong-password, or inactive users.
4. React calls `GET /api/v1/auth/me` with `Authorization: Bearer <access>`, keeps the access token in memory, and refreshes it before its five-minute expiry. On page reload, it obtains a CSRF token and uses the HttpOnly refresh cookie to restore the session.
5. Refresh and logout require CSRF validation because they rely on a browser cookie. A missing/invalid/expired/blacklisted refresh credential returns `401`; a CSRF failure returns `403`.
6. Logout revokes refresh and clears the cookie. Already issued access tokens expire within five minutes; they are not immediately revoked server-side.

## API errors

Responses use `{ "error": { "code": "...", "message": "...", "details": ..., "request_id": "..." } }`. Malformed input is `400`, missing/invalid credentials are `401`, CSRF or role denial is `403`, and throttled authentication attempts are `429`. Login credential failures do not reveal whether an email exists or an account is inactive. Unexpected errors are sanitized and logs include only request correlation and exception type.

## Throttling and integration validation

Login and refresh use DRF `ScopedRateThrottle` with production application scopes `auth_login` (10 requests/minute) and `auth_refresh` (30 requests/minute). DRF stores throttle counters through Django's default cache. The configured backend is `django.core.cache.backends.redis.RedisCache`, using `DJANGO_CACHE_URL` or `redis://<REDIS_HOST>:<REDIS_PORT>/2`; anonymous auth requests are limited by their requester/IP identity. This Redis database is separate from Celery broker `/0` and result backend `/1`.

Fast tests use the explicit `settings.test` module (in-memory SQLite and locmem cache). PostgreSQL/Redis integration tests use `settings.test_postgres`, which restores the environment-configured PostgreSQL database and Redis cache and fails closed if the requested database/cache configuration is not present. In this mode Django creates a disposable test database; tests check the live database vendor, Redis read/write, and actual login throttling. The exact Compose command and browser smoke checklist are in [the development environment guide](../development-environment.md). Local SQLite results are not PostgreSQL/Redis validation.

The login-throttle integration test applies its 1/minute test rate to the actual imported `ScopedRateThrottle` rate map. DRF copies the configured rate map onto the class at import time; changing `REST_FRAMEWORK` with a later test settings override does not retroactively update that map. The test asserts that the first request consumes one Redis history entry and a second request from the same IP receives `429`. The developer reports this test passed in the Windows Docker PostgreSQL/Redis integration run. Application rates remain unchanged at 10/minute for login and 30/minute for refresh.

### Phase 4 validation record

The developer reports that the Windows Docker environment had all six Compose services healthy, PostgreSQL migrations applied, and PostgreSQL/Redis integration settings active. The full backend integration run passed 39 tests, including authentication API, token refresh/rotation/blacklisting, role authorization, and Redis-backed login throttling. Browser login reached the authenticated application shell. Codex did not independently execute Docker or browser checks in this workspace; see [project status](../../PROJECT_STATUS.md). These results validate the reported development stack only and do not constitute production deployment or security certification.

## Password and account controls

Passwords are hashed by Django's configured password hasher. The Django validators require at least 12 characters and reject common/numeric-only/similar passwords when accounts are created through the application manager or Django's supported account tools. Password reset and email verification are later work. Account provisioning remains college-administered; demo accounts are available only through the development-only `seed_demo` command.

## Authorization and permissions

DRF globally authenticates bearer access JWTs and requires `IsAuthenticated` by default. The public health, CSRF, login, refresh, and logout endpoints explicitly opt out where needed. Reusable `IsAdminRole`, `IsTeacherRole`, and `IsAdminOrTeacherRole` permissions establish coarse role checks. They do not implement lecture assignment or cross-object scope; those rules remain in later management/resource slices and must be enforced server-side there.

See [authorization.md](authorization.md) and [API contracts](api-contracts.md) for the initial role matrix and endpoint contracts.

## Audit events

Authentication audit writes are deferred to the Phase 5 Operations/Audit integration before user-management APIs are exposed. The current `AuditEvent` model can represent outcomes, but automatic writes for every invalid login/refresh require a retention policy, alerting thresholds, and abuse/failure volume limits. Do not store email/password/token values in audit metadata. This deferral does not add credentials to application logs.
