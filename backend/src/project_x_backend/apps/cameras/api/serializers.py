import re
from decimal import Decimal

from rest_framework import serializers

from project_x_backend.apps.cameras.models import Camera
from project_x_backend.apps.classrooms.models import Classroom


class CameraClassroomSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="pk")
    code = serializers.CharField()
    name = serializers.CharField()


class CameraReadSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="identifier")
    classroom_id = serializers.UUIDField(read_only=True)
    classroom = CameraClassroomSerializer(read_only=True)
    resolution = serializers.SerializerMethodField()
    frame_rate = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Camera
        fields = (
            "id",
            "code",
            "display_name",
            "classroom_id",
            "classroom",
            "source_type",
            "status",
            "resolution",
            "frame_rate",
            "description",
            "created_at",
            "updated_at",
        )

    def get_resolution(self, obj) -> str | None:
        return obj.metadata.get("resolution")

    def get_frame_rate(self, obj) -> Decimal | None:
        return obj.metadata.get("frame_rate")

    def get_description(self, obj) -> str:
        return obj.metadata.get("description", "")


class CameraWriteSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=80, required=True)
    display_name = serializers.CharField(max_length=120, required=True)
    classroom_id = serializers.UUIDField(required=True, write_only=True)
    source_type = serializers.ChoiceField(choices=Camera.SourceType.choices, required=False)
    status = serializers.ChoiceField(choices=Camera.Status.choices, required=False)
    resolution = serializers.CharField(
        max_length=32, required=False, allow_blank=True, allow_null=True
    )
    frame_rate = serializers.DecimalField(
        max_digits=8,
        decimal_places=3,
        min_value=Decimal("0.001"),
        required=False,
        allow_null=True,
    )
    description = serializers.CharField(
        max_length=500, required=False, allow_blank=True, allow_null=True
    )

    def validate_code(self, value):
        value = value.strip()
        queryset = Camera.objects.filter(identifier__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A camera with this code already exists.")
        return value

    def validate_classroom_id(self, value):
        if self.instance:
            raise serializers.ValidationError("A camera cannot be moved to another classroom.")
        if not Classroom.objects.filter(
            pk=value, institution_id=self.context["institution_id"]
        ).exists():
            raise serializers.ValidationError("The selected classroom is not available.")
        return value

    def validate_source_type(self, value):
        if value != Camera.SourceType.LOCAL_FILE:
            raise serializers.ValidationError(
                "Only LOCAL_FILE metadata is supported in this phase."
            )
        return value

    def validate_resolution(self, value):
        if value in (None, ""):
            return value
        match = re.fullmatch(r"\s*([1-9][0-9]{0,4})\s*[xX×]\s*([1-9][0-9]{0,4})\s*", value)
        if not match:
            raise serializers.ValidationError("Use a width x height value, such as 1920x1080.")
        return f"{int(match.group(1))}x{int(match.group(2))}"

    def validate(self, attrs):
        unexpected = set(self.initial_data) - {
            "code",
            "display_name",
            "classroom_id",
            "source_type",
            "status",
            "resolution",
            "frame_rate",
            "description",
        }
        if unexpected:
            raise serializers.ValidationError(
                {field: "This field is not accepted." for field in sorted(unexpected)}
            )
        if not self.instance:
            attrs.setdefault("source_type", Camera.SourceType.LOCAL_FILE)
            attrs.setdefault("status", Camera.Status.ACTIVE)
        return attrs
