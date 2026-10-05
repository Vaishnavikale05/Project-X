from rest_framework import serializers

from project_x_backend.apps.institutions.models import Institution


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ("id", "name", "code", "timezone", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_code(self, value):
        qs = Institution.objects.filter(code__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("An institution with this code already exists.")
        return value.strip()

    def validate(self, attrs):
        unexpected = set(self.initial_data) - {"name", "code", "timezone", "is_active"}
        if unexpected:
            raise serializers.ValidationError(
                {field: "This field is not accepted." for field in sorted(unexpected)}
            )
        return attrs

    def validate_timezone(self, value):
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise serializers.ValidationError("Enter a valid IANA time zone.") from exc
        return value
