import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Recommendation(models.Model):
    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "High"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        DISMISSED = "DISMISSED", "Dismissed"
        EXPIRED = "EXPIRED", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lecture = models.ForeignKey(
        "lectures.Lecture", on_delete=models.PROTECT, related_name="recommendations"
    )
    analytics_run = models.ForeignKey(
        "analytics.AnalyticsRun", on_delete=models.PROTECT, related_name="recommendations"
    )
    recommendation_type = models.CharField(max_length=64)
    rule_id = models.CharField(max_length=100)
    observation = models.CharField(max_length=500)
    content = models.TextField()
    evidence_refs = models.JSONField(default=list, blank=True)
    priority = models.CharField(max_length=8, choices=Priority.choices, default=Priority.NORMAL)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["analytics_run", "rule_id"], name="recommendation_run_rule_uniq"
            ),
            models.CheckConstraint(
                condition=Q(status__in=["ACTIVE", "DISMISSED", "EXPIRED"]),
                name="recommendation_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(priority__in=["LOW", "NORMAL", "HIGH"]),
                name="recommendation_priority_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["lecture", "status", "created_at"], name="recommend_lecture_status_idx"
            )
        ]

    def __str__(self) -> str:
        return f"{self.recommendation_type}: {self.rule_id}"

    def clean(self):
        super().clean()
        if (
            self.lecture_id
            and self.analytics_run_id
            and self.analytics_run.lecture_id != self.lecture_id
        ):
            raise ValidationError(
                {"analytics_run": "Recommendation analytics must belong to the same lecture."}
            )
