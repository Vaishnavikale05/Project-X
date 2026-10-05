"""Checks that run only in the explicit PostgreSQL/Redis integration mode."""

from unittest import skipUnless
from unittest.mock import patch
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from project_x_backend.apps.accounts.api.views import AuthLoginView
from project_x_backend.apps.accounts.models import User
from project_x_backend.apps.institutions.models import Institution


@skipUnless(
    getattr(settings, "PROJECT_X_INTEGRATION_MODE", None) == "postgres",
    "Run with project_x_backend.config.settings.test_postgres to use PostgreSQL/Redis.",
)
class PostgreSQLRedisIntegrationTests(TestCase):
    """Exercise the real configured database, Redis cache, and DRF login throttle."""

    @classmethod
    def setUpTestData(cls):
        cls.institution = Institution.objects.create(
            name="Throttle Test College", code="THROTTLE-T"
        )
        cls.user = User.objects.create_user(
            email="throttle@example.invalid",
            password="Secur3-College-Auth-Passphrase!",
            display_name="Throttle Test",
            institution=cls.institution,
            role=User.Role.ADMIN,
        )

    def test_database_and_cache_are_postgresql_and_redis(self):
        self.assertEqual(connection.vendor, "postgresql")
        key = f"project-x:integration:{uuid4()}"
        cache.set(key, "redis-ready", timeout=30)
        self.assertEqual(cache.get(key), "redis-ready")
        cache.delete(key)

    def test_login_throttle_uses_the_redis_backed_cache(self):
        client = APIClient(enforce_csrf_checks=True)
        csrf = client.get("/api/v1/auth/csrf/").json()["csrf_token"]
        nonce = uuid4().int
        client_ip = f"198.51.{(nonce >> 8) % 256}.{nonce % 256}"
        payload = {"email": self.user.email, "password": "Secur3-College-Auth-Passphrase!"}
        headers = {"HTTP_X_CSRFTOKEN": csrf, "REMOTE_ADDR": client_ip}
        original_rates = ScopedRateThrottle.THROTTLE_RATES
        test_rates = {**original_rates, "auth_login": "1/min"}
        throttle_key = ScopedRateThrottle.cache_format % {
            "scope": "auth_login",
            "ident": client_ip,
        }

        # ScopedRateThrottle snapshots DEFAULT_THROTTLE_RATES on its class at import time.
        # override_settings alone does not change the map used by this already-imported class.
        with patch.object(ScopedRateThrottle, "THROTTLE_RATES", test_rates):
            first = client.post("/api/v1/auth/login", payload, format="json", **headers)
            history_after_first = cache.get(throttle_key)
            second = client.post("/api/v1/auth/login", payload, format="json", **headers)
            history_after_second = cache.get(throttle_key)

        self.assertEqual(AuthLoginView.throttle_classes, [ScopedRateThrottle])
        self.assertEqual(AuthLoginView.throttle_scope, "auth_login")
        self.assertEqual(original_rates["auth_login"], "10/min")
        self.assertEqual(first.wsgi_request.META["REMOTE_ADDR"], client_ip)
        self.assertEqual(second.wsgi_request.META["REMOTE_ADDR"], client_ip)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(history_after_first), 1)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(history_after_second, history_after_first)
        self.assertEqual(ScopedRateThrottle.THROTTLE_RATES, original_rates)
