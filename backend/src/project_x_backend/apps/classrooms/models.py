import uuid

from django.db import models
from django.db.models import F
from django.db.models.functions import Lower


class Classroom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(
        "institutions.Institution", on_delete=models.PROTECT, related_name="classrooms"
    )
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=120, blank=True)
    capacity = models.PositiveSmallIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["institution__code", "code"]
        constraints = [
            models.UniqueConstraint(
                Lower("code"), F("institution"), name="classroom_institution_code_ci_uniq"
            ),
            models.CheckConstraint(
                condition=models.Q(capacity__isnull=True) | models.Q(capacity__gt=0),
                name="classroom_capacity_positive",
            ),
        ]
        indexes = [
            models.Index(fields=["institution", "is_active"], name="classroom_inst_active_idx")
        ]

    def __str__(self) -> str:
        return self.name or self.code
