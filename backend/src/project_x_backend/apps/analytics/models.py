import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class AnalyticsRun(models.Model):
    class Status(models.TextChoices):
        GENERATED = "GENERATED", "Generated"
        READY = "READY", "Ready"
        SUPERSEDED = "SUPERSEDED", "Superseded"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lecture = models.ForeignKey(
        "lectures.Lecture", on_delete=models.PROTECT, related_name="analytics_runs"
    )
    processing_job = models.ForeignKey(
        "processing.ProcessingJob", on_delete=models.PROTECT, related_name="analytics_runs"
    )
    input_cv_run = models.ForeignKey(
        "processing.CVRun", on_delete=models.PROTECT, related_name="analytics_runs"
    )
    rule_set_version = models.CharField(max_length=80)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.GENERATED)
    limitations = models.JSONField(default=list, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["GENERATED", "READY", "SUPERSEDED", "FAILED"]),
                name="analytics_run_status_valid",
            )
        ]
        indexes = [
            models.Index(
                fields=["lecture", "status", "generated_at"], name="analytics_run_lecture_idx"
            )
        ]

    def clean(self):
        super().clean()
        if (
            self.processing_job_id
            and self.input_cv_run_id
            and self.input_cv_run.processing_job_id != self.processing_job_id
        ):
            raise ValidationError(
                {"input_cv_run": "CV output must come from the selected processing job."}
            )
        if (
            self.lecture_id
            and self.processing_job_id
            and self.processing_job.footage.lecture_id != self.lecture_id
        ):
            raise ValidationError(
                {"processing_job": "Processing job footage must belong to the selected lecture."}
            )


class IndicatorAggregate(models.Model):
    class IndicatorCode(models.TextChoices):
        ATTENTION = "ATTENTION", "Attention indicator"
        DROWSINESS = "DROWSINESS", "Drowsiness indicator"
        DISTRACTION = "DISTRACTION", "Distraction indicator"
        ENGAGEMENT = "ENGAGEMENT", "Engagement-related score"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analytics_run = models.ForeignKey(
        AnalyticsRun, on_delete=models.PROTECT, related_name="indicators"
    )
    indicator_code = models.CharField(max_length=20, choices=IndicatorCode.choices)
    window_start = models.DateTimeField()
    window_end = models.DateTimeField()
    value = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    unit = models.CharField(max_length=32, blank=True)
    coverage = models.DecimalField(max_digits=6, decimal_places=5, null=True, blank=True)
    confidence_summary = models.DecimalField(max_digits=6, decimal_places=5, null=True, blank=True)
    sample_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["window_start", "indicator_code"]
        constraints = [
            models.UniqueConstraint(
                fields=["analytics_run", "indicator_code", "window_start"],
                name="indicator_run_code_window_uniq",
            ),
            models.CheckConstraint(
                condition=Q(
                    indicator_code__in=["ATTENTION", "DROWSINESS", "DISTRACTION", "ENGAGEMENT"]
                ),
                name="indicator_code_valid",
            ),
            models.CheckConstraint(
                condition=Q(window_end__gt=models.F("window_start")), name="indicator_window_valid"
            ),
            models.CheckConstraint(
                condition=(Q(coverage__isnull=True) | Q(coverage__gte=0, coverage__lte=1))
                & (
                    Q(confidence_summary__isnull=True)
                    | Q(confidence_summary__gte=0, confidence_summary__lte=1)
                ),
                name="indicator_quality_range",
            ),
        ]
        indexes = [
            models.Index(fields=["analytics_run", "window_start"], name="indicator_run_time_idx")
        ]
