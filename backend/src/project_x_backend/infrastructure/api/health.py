"""Minimal anonymous infrastructure readiness endpoint."""

from django.conf import settings
from django.db import connection
from drf_spectacular.utils import extend_schema
from redis import Redis
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ok", "degraded"])
    dependencies = serializers.DictField(
        child=serializers.ChoiceField(choices=["ok", "unavailable"])
    )
    request_id = serializers.UUIDField(allow_null=True)


def dependency_status() -> dict[str, str]:
    states = {"database": "unavailable", "redis": "unavailable"}
    try:
        connection.ensure_connection()
        states["database"] = "ok"
    except Exception:  # noqa: BLE001 - readiness reports outage without leaking details
        pass
    try:
        client = Redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=1)
        client.ping()
        states["redis"] = "ok"
    except Exception:  # noqa: BLE001 - readiness reports outage without leaking details
        pass
    return states


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="getHealth",
        summary="Check application and infrastructure readiness",
        responses={200: HealthResponseSerializer, 503: HealthResponseSerializer},
    )
    def get(self, request):
        dependencies = dependency_status()
        healthy = all(value == "ok" for value in dependencies.values())
        return Response(
            {
                "status": "ok" if healthy else "degraded",
                "dependencies": dependencies,
                "request_id": getattr(request, "request_id", None),
            },
            status=200 if healthy else 503,
        )
