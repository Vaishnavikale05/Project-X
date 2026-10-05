"""Shared API transport serializers."""

from rest_framework import serializers


class ApiErrorDetailSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.JSONField(allow_null=True)
    request_id = serializers.CharField(allow_null=True)


class ApiErrorSerializer(serializers.Serializer):
    error = ApiErrorDetailSerializer()
