"""Isolated test settings; no local PostgreSQL/Redis services are required."""

from .base import *  # noqa: F403
from .base import SIMPLE_JWT as BASE_SIMPLE_JWT

SECRET_KEY = "test-only-not-a-secret"
DEBUG = False
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
PROJECT_X_INTEGRATION_MODE = "sqlite"
AUTH_REFRESH_COOKIE_SECURE = False
JWT_SIGNING_KEY = SECRET_KEY
SIMPLE_JWT = {**BASE_SIMPLE_JWT, "SIGNING_KEY": SECRET_KEY}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
