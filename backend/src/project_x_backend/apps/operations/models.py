import uuid

from django.db import models


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    institution = models.ForeignKey(
        "institutions.Institution",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="audit_events",
    )
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100)
    object_id = models.UUIDField(null=True, blank=True)
    request_id = models.CharField(max_length=100, blank=True)
    metadata_redacted = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["institution", "occurred_at"], name="audit_institution_time_idx"),
            models.Index(fields=["actor", "occurred_at"], name="audit_actor_time_idx"),
            models.Index(fields=["object_type", "object_id"], name="audit_object_idx"),
        ]
