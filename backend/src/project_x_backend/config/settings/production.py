"""Production-safe defaults. Deployment-specific secrets must be injected."""

from .base import *  # noqa: F403

DEBUG = False
if not SECRET_KEY:  # noqa: F405
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production")
JWT_SIGNING_KEY = env("JWT_SIGNING_KEY", default="")  # noqa: F405
if not JWT_SIGNING_KEY:
    raise RuntimeError("JWT_SIGNING_KEY must be set in production")
SIMPLE_JWT = {**SIMPLE_JWT, "SIGNING_KEY": JWT_SIGNING_KEY}  # noqa: F405
AUTH_REFRESH_COOKIE_SECURE = True  # noqa: F405
CSRF_COOKIE_SECURE = True
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])  # noqa: F405
if not ALLOWED_HOSTS:
    raise RuntimeError("DJANGO_ALLOWED_HOSTS must contain approved hostnames")

database = DATABASES["default"]  # noqa: F405
if not all(database[field] for field in ("NAME", "USER", "PASSWORD", "HOST")):
    raise RuntimeError(
        "PostgreSQL connection settings must be provided through environment variables"
    )

REDIS_HOST = env("REDIS_HOST", default="")  # noqa: F405
if not REDIS_HOST:
    raise RuntimeError("REDIS_HOST must be set in production")
REDIS_PORT = env.int("REDIS_PORT", default=6379)  # noqa: F405
CELERY_BROKER_URL = env(  # noqa: F405
    "CELERY_BROKER_URL", default=f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
)
CELERY_RESULT_BACKEND = env(  # noqa: F405
    "CELERY_RESULT_BACKEND", default=f"redis://{REDIS_HOST}:{REDIS_PORT}/1"
)

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("DJANGO_HSTS_SECONDS", default=0)  # noqa: F405
if SECURE_HSTS_SECONDS <= 0:
    raise RuntimeError(
        "DJANGO_HSTS_SECONDS must be explicitly set to a positive value in production"
    )
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("DJANGO_HSTS_INCLUDE_SUBDOMAINS", default=False)  # noqa: F405
SECURE_HSTS_PRELOAD = env.bool("DJANGO_HSTS_PRELOAD", default=False)  # noqa: F405
