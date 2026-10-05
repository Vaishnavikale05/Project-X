import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Footage(models.Model):
    class StorageProvider(models.TextChoices):
        LOCAL_FILE = "LOCAL_FILE", "Local file"

    class Status(models.TextChoices):
        DISCOVERED = "DISCOVERED", "Discovered"
        VALIDATING = "VALIDATING", "Validating"
        STORED = "STORED", "Stored"
        QUEUED = "QUEUED", "Queued"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        VALIDATION_FAILED = "VALIDATION_FAILED", "Validation failed"
        PROCESSING_FAILED = "PROCESSING_FAILED", "Processing failed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lecture = models.ForeignKey(
        "lectures.Lecture", on_delete=models.PROTECT, related_name="footage"
    )
    camera = models.ForeignKey("cameras.Camera", on_delete=models.PROTECT, related_name="footage")
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255, blank=True)
    storage_provider = models.CharField(
        max_length=24, choices=StorageProvider.choices, default=StorageProvider.LOCAL_FILE
    )
    storage_key = models.CharField(max_length=512, null=True, blank=True)
    size_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    media_format = models.CharField(max_length=32, blank=True)
    media_type = models.CharField(max_length=100, blank=True)
    width = models.PositiveSmallIntegerField(null=True, blank=True)
    height = models.PositiveSmallIntegerField(null=True, blank=True)
    frame_rate = models.DecimalField(max_digits=7, decimal_places=3, null=True, blank=True)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    recorded_start = models.DateTimeField(null=True, blank=True)
    recorded_end = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveBigIntegerField(null=True, blank=True)
    ingested_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DISCOVERED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["storage_provider", "storage_key"],
                condition=Q(storage_key__isnull=False),
                name="footage_storage_reference_uniq",
            ),
            models.CheckConstraint(
                condition=(
                    Q(recorded_start__isnull=True, recorded_end__isnull=True)
                    | Q(
                        recorded_start__isnull=False,
                        recorded_end__isnull=False,
                        recorded_start__lt=models.F("recorded_end"),
                    )
                ),
                name="footage_recorded_interval_valid",
            ),
            models.CheckConstraint(
                condition=Q(duration_ms__isnull=True) | Q(duration_ms__gt=0),
                name="footage_duration_positive",
            ),
            models.CheckConstraint(
                condition=Q(frame_rate__isnull=True) | Q(frame_rate__gt=0),
                name="footage_frame_rate_positive",
            ),
            models.CheckConstraint(
                condition=Q(storage_provider="LOCAL_FILE"), name="footage_provider_valid"
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "DISCOVERED",
                        "VALIDATING",
                        "STORED",
                        "QUEUED",
                        "PROCESSING",
                        "COMPLETED",
                        "VALIDATION_FAILED",
                        "PROCESSING_FAILED",
                        "CANCELLED",
                    ]
                ),
                name="footage_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["DISCOVERED", "VALIDATING", "VALIDATION_FAILED"])
                | Q(storage_key__isnull=False),
                name="footage_stored_state_has_key",
            ),
        ]
        indexes = [
            models.Index(fields=["lecture", "status"], name="footage_lecture_status_idx"),
            models.Index(fields=["camera", "recorded_start"], name="footage_camera_time_idx"),
            models.Index(fields=["checksum_sha256"], name="footage_checksum_idx"),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if (
            self.camera_id
            and self.lecture_id
            and self.camera.classroom_id != self.lecture.classroom_id
        ):
            errors["camera"] = "Camera must belong to the lecture classroom."
        if self.recorded_start and self.recorded_end and self.recorded_start >= self.recorded_end:
            errors["recorded_end"] = "Must be after recorded start."
        if bool(self.recorded_start) != bool(self.recorded_end):
            errors["recorded_end"] = "Recorded start and end must be provided together."
        if self.checksum_sha256 and (
            len(self.checksum_sha256) != 64
            or any(c not in "0123456789abcdefABCDEF" for c in self.checksum_sha256)
        ):
            errors["checksum_sha256"] = "Expected a SHA-256 hexadecimal digest."
        if self.duration_ms is not None and self.duration_ms <= 0:
            errors["duration_ms"] = "Duration must be positive."
        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return self.filename
