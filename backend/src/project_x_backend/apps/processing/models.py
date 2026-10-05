import uuid

from django.db import models
from django.db.models import Q


class ProcessingJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        QUEUED = "QUEUED", "Queued"
        PROCESSING = "PROCESSING", "Processing"
        RETRY_WAIT = "RETRY_WAIT", "Retry wait"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    footage = models.ForeignKey(
        "footage.Footage", on_delete=models.PROTECT, related_name="processing_jobs"
    )
    job_type = models.CharField(max_length=40, default="LECTURE_ANALYSIS")
    idempotency_key = models.CharField(max_length=128)
    pipeline_version = models.CharField(max_length=80, blank=True)
    config_digest = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=3)
    queued_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_code = models.CharField(max_length=64, blank=True)
    safe_error_summary = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["footage", "idempotency_key"], name="job_footage_idempotency_uniq"
            ),
            models.CheckConstraint(
                condition=Q(max_attempts__gt=0), name="job_max_attempts_positive"
            ),
            models.CheckConstraint(
                condition=Q(attempt_count__lte=models.F("max_attempts")),
                name="job_attempt_count_bounded",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "PENDING",
                        "QUEUED",
                        "PROCESSING",
                        "RETRY_WAIT",
                        "COMPLETED",
                        "FAILED",
                        "CANCELLED",
                    ]
                ),
                name="job_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "created_at"], name="job_status_created_idx"),
            models.Index(fields=["footage", "created_at"], name="job_footage_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.job_type} {self.id} ({self.status})"


class ProcessingLog(models.Model):
    class Level(models.TextChoices):
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        ERROR = "ERROR", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    processing_job = models.ForeignKey(ProcessingJob, on_delete=models.PROTECT, related_name="logs")
    attempt_number = models.PositiveSmallIntegerField(default=0)
    level = models.CharField(max_length=8, choices=Level.choices, default=Level.INFO)
    event_code = models.CharField(max_length=64)
    message_safe = models.CharField(max_length=500)
    details_redacted = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["occurred_at"]
        indexes = [
            models.Index(
                fields=["processing_job", "occurred_at"], name="processing_log_job_time_idx"
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(level__in=["INFO", "WARNING", "ERROR"]),
                name="processing_log_level_valid",
            )
        ]


class CVRun(models.Model):
    class Status(models.TextChoices):
        PRODUCED = "PRODUCED", "Produced"
        VALIDATED = "VALIDATED", "Validated"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    processing_job = models.ForeignKey(
        ProcessingJob, on_delete=models.PROTECT, related_name="cv_runs"
    )
    contract_version = models.CharField(max_length=40, default="cv-observations/v1")
    schema_version = models.PositiveSmallIntegerField(default=1)
    pipeline_version = models.CharField(max_length=80)
    model_versions = models.JSONField(default=dict)
    sampling_policy = models.CharField(max_length=80)
    coverage = models.JSONField(default=dict)
    artifact_storage_provider = models.CharField(max_length=24, blank=True)
    artifact_storage_key = models.CharField(max_length=512, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PRODUCED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["processing_job", "schema_version"], name="cv_run_job_schema_uniq"
            ),
            models.CheckConstraint(
                condition=Q(status__in=["PRODUCED", "VALIDATED", "REJECTED"]),
                name="cv_run_status_valid",
            ),
        ]
        indexes = [models.Index(fields=["processing_job", "status"], name="cv_run_job_status_idx")]


class CVObservation(models.Model):
    class EyeState(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        UNKNOWN = "unknown", "Unknown"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv_run = models.ForeignKey(CVRun, on_delete=models.PROTECT, related_name="observations")
    window_start_ms = models.PositiveBigIntegerField()
    window_end_ms = models.PositiveBigIntegerField()
    track_ref = models.CharField(max_length=100, blank=True)
    face_visible = models.BooleanField(null=True, blank=True)
    face_visibility_confidence = models.DecimalField(
        max_digits=6, decimal_places=5, null=True, blank=True
    )
    head_yaw_deg = models.DecimalField(max_digits=7, decimal_places=3, null=True, blank=True)
    head_pitch_deg = models.DecimalField(max_digits=7, decimal_places=3, null=True, blank=True)
    head_confidence = models.DecimalField(max_digits=6, decimal_places=5, null=True, blank=True)
    eye_state = models.CharField(max_length=8, choices=EyeState.choices, blank=True)
    eye_state_confidence = models.DecimalField(
        max_digits=6, decimal_places=5, null=True, blank=True
    )
    quality_flags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["cv_run", "window_start_ms", "track_ref"]
        constraints = [
            models.CheckConstraint(
                condition=Q(window_end_ms__gt=models.F("window_start_ms")),
                name="cv_observation_window_valid",
            ),
            models.CheckConstraint(
                condition=Q(eye_state__in=["", "open", "closed", "unknown"]),
                name="cv_observation_eye_state_valid",
            ),
            models.CheckConstraint(
                condition=(
                    Q(face_visibility_confidence__isnull=True)
                    | Q(face_visibility_confidence__gte=0, face_visibility_confidence__lte=1)
                )
                & (
                    Q(head_confidence__isnull=True)
                    | Q(head_confidence__gte=0, head_confidence__lte=1)
                )
                & (
                    Q(eye_state_confidence__isnull=True)
                    | Q(eye_state_confidence__gte=0, eye_state_confidence__lte=1)
                ),
                name="cv_observation_confidence_range",
            ),
        ]
        indexes = [
            models.Index(fields=["cv_run", "window_start_ms"], name="cv_observation_run_time_idx")
        ]
