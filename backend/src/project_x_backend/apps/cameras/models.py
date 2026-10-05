import uuid

from django.db import models
from django.db.models.functions import Lower


class Camera(models.Model):
    class SourceType(models.TextChoices):
        LOCAL_FILE = "LOCAL_FILE", "Local file"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey(
        "classrooms.Classroom", on_delete=models.PROTECT, related_name="cameras"
    )
    identifier = models.CharField(max_length=80)
    display_name = models.CharField(max_length=120)
    source_type = models.CharField(
        max_length=24, choices=SourceType.choices, default=SourceType.LOCAL_FILE
    )
    source_reference = models.CharField(
        max_length=500,
        blank=True,
        help_text="Non-secret provider reference only; never store credentials here.",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Non-secret technical metadata only; never store credentials.",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["classroom", "identifier"]
        constraints = [
            models.UniqueConstraint(Lower("identifier"), name="camera_identifier_casefold_uniq"),
            models.CheckConstraint(
                condition=models.Q(source_type="LOCAL_FILE"), name="camera_source_type_valid"
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["ACTIVE", "INACTIVE"]), name="camera_status_valid"
            ),
        ]
        indexes = [models.Index(fields=["classroom", "status"], name="camera_classroom_status_idx")]

    def __str__(self) -> str:
        return self.identifier
