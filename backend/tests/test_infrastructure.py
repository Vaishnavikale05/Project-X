from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

import yaml
from django.test import Client, RequestFactory, TestCase
from rest_framework import status

from project_x_backend.infrastructure.api.exceptions import api_exception_handler
from project_x_backend.infrastructure.storage.local import LocalFileStorage


class InfrastructureTests(TestCase):
    def test_public_health_endpoint_reports_dependencies_without_secrets(self):
        with patch(
            "project_x_backend.infrastructure.api.health.dependency_status",
            return_value={"database": "ok", "redis": "ok"},
        ):
            response = Client().get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response["X-Request-ID"], response.json()["request_id"])
        self.assertNotIn("password", response.content.decode().lower())

    def test_health_endpoint_is_degraded_when_dependency_is_unavailable(self):
        with patch(
            "project_x_backend.infrastructure.api.health.dependency_status",
            return_value={"database": "unavailable", "redis": "ok"},
        ):
            response = Client().get("/api/v1/health")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "degraded")

    def test_versioned_openapi_schema_is_served(self):
        response = Client().get("/api/v1/schema/")

        self.assertEqual(response.status_code, 200)
        schema = yaml.safe_load(response.content)
        self.assertIn("/api/v1/health", schema["paths"])

    def test_unhandled_api_errors_are_sanitized_and_correlated(self):
        request = RequestFactory().get("/api/v1/example")
        request.request_id = "request-123"

        response = api_exception_handler(
            RuntimeError("sensitive internal details"), {"request": request}
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"]["request_id"], "request-123")
        self.assertIsNone(response.data["error"]["details"])
        self.assertNotIn("sensitive", str(response.data))

    def test_local_file_storage_round_trips_and_computes_metadata(self):
        with TemporaryDirectory() as storage_root:
            storage = LocalFileStorage(storage_root)
            stored = storage.save(BytesIO(b"sample recorded bytes"), suffix=".mp4")

            self.assertEqual(stored.provider, "local")
            self.assertTrue(storage.exists(stored.key))
            with storage.retrieve(stored.key) as video:
                self.assertEqual(video.read(), b"sample recorded bytes")
            metadata = storage.metadata(stored.key)
            self.assertEqual(metadata.size_bytes, stored.size_bytes)
            self.assertEqual(metadata.checksum_sha256, stored.checksum_sha256)
            self.assertTrue(storage.delete(stored.key))
            self.assertFalse(storage.exists(stored.key))

    def test_local_file_storage_rejects_path_traversal(self):
        with TemporaryDirectory() as storage_root:
            storage = LocalFileStorage(storage_root)

            with self.assertRaises(ValueError):
                storage.exists("../outside")
