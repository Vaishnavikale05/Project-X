import uuid

from django.core.exceptions import ValidationError
from django.db import models


class LectureSummary(models.Model):
    """Versioned, materialized lecture summary sourced from one analytics run."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lecture = models.ForeignKey(
        "lectures.Lecture", on_delete=models.PROTECT, related_name="summaries"
    )
    analytics_run = models.OneToOneField(
        "analytics.AnalyticsRun", on_delete=models.PROTECT, related_name="lecture_summary"
    )
    average_attention = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    average_drowsiness = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    average_distraction = models.DecimalField(
        max_digits=12, decimal_places=5, null=True, blank=True
    )
    overall_engagement = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    analysis_completed_at = models.DateTimeField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["lecture", "generated_at"], name="summary_lecture_generated_idx")
        ]

    def clean(self):
        super().clean()
        if (
            self.lecture_id
            and self.analytics_run_id
            and self.analytics_run.lecture_id != self.lecture_id
        ):
            raise ValidationError(
                {"analytics_run": "Summary analytics must belong to the same lecture."}
            )


class LectureReport(models.Model):
    class Status(models.TextChoices):
        GENERATED = "GENERATED", "Generated"
        SUPERSEDED = "SUPERSEDED", "Superseded"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lecture = models.ForeignKey(
        "lectures.Lecture", on_delete=models.PROTECT, related_name="reports"
    )
    analytics_run = models.ForeignKey(
        "analytics.AnalyticsRun", on_delete=models.PROTECT, related_name="reports"
    )
    report_version = models.PositiveSmallIntegerField(default=1)
    summary_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.GENERATED)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["lecture", "analytics_run", "report_version"],
                name="report_lecture_run_version_uniq",
            ),
            models.CheckConstraint(
                condition=models.Q(report_version__gt=0), name="report_version_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["GENERATED", "SUPERSEDED", "FAILED"]),
                name="report_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["lecture", "generated_at"], name="report_lecture_generated_idx")
        ]

    def clean(self):
        super().clean()
        if (
            self.lecture_id
            and self.analytics_run_id
            and self.analytics_run.lecture_id != self.lecture_id
        ):
            raise ValidationError(
                {"analytics_run": "Report analytics must belong to the same lecture."}
            )
