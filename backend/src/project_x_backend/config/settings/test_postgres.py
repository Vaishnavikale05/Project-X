"""Explicit PostgreSQL and Redis integration-test settings.

Django creates a separate test database on the configured PostgreSQL server.
This module intentionally fails closed instead of falling back to SQLite.
"""

from copy import deepcopy

from django.core.exceptions import ImproperlyConfigured

from .base import CACHES as BASE_CACHES
from .base import DATABASES as BASE_DATABASES
from .test import *  # noqa: F403

DATABASES = deepcopy(BASE_DATABASES)
CACHES = deepcopy(BASE_CACHES)
PROJECT_X_INTEGRATION_MODE = "postgres"

database = DATABASES["default"]
if database["ENGINE"] != "django.db.backends.postgresql":
    raise ImproperlyConfigured(
        "PostgreSQL integration tests require the PostgreSQL database backend."
    )

missing_database_settings = [
    key for key in ("NAME", "USER", "PASSWORD", "HOST", "PORT") if not database.get(key)
]
if missing_database_settings:
    raise ImproperlyConfigured(
        "PostgreSQL integration tests require environment settings for: "
        + ", ".join(missing_database_settings)
    )

if CACHES["default"]["BACKEND"] != "django.core.cache.backends.redis.RedisCache":
    raise ImproperlyConfigured(
        "PostgreSQL integration tests require the configured Redis cache backend."
    )
