from rest_framework import serializers

from project_x_backend.apps.classrooms.models import Classroom


class InstitutionBriefSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="pk")
    code = serializers.CharField()
    name = serializers.CharField()


class ClassroomReadSerializer(serializers.ModelSerializer):
    institution = InstitutionBriefSerializer(read_only=True)

    class Meta:
        model = Classroom
        fields = (
            "id",
            "institution",
            "code",
            "name",
            "capacity",
            "is_active",
            "created_at",
            "updated_at",
        )


class ClassroomWriteSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=40)
    name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    capacity = serializers.IntegerField(
        required=False, allow_null=True, min_value=1, max_value=32767
    )
    is_active = serializers.BooleanField(required=False)

    def validate_code(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Room code is required.")
        queryset = Classroom.objects.filter(
            institution_id=self.context["institution_id"], code__iexact=value
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A classroom with this code already exists.")
        return value

    def validate(self, attrs):
        unexpected = set(self.initial_data) - {"code", "name", "capacity", "is_active"}
        if unexpected:
            raise serializers.ValidationError(
                {
                    field: "Institution scope is derived from the authenticated account."
                    if field in {"institution", "institution_id"}
                    else "This field is not accepted."
                    for field in sorted(unexpected)
                }
            )
        return attrs
