import uuid

from django.db import models
from django.db.models.functions import Lower


class Institution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=40, unique=True)
    timezone = models.CharField(max_length=64, default="UTC")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(Lower("code"), name="institution_code_casefold_uniq")
        ]
        indexes = [models.Index(fields=["is_active", "name"], name="institution_active_name_idx")]

    def __str__(self) -> str:
        return f"{self.code}: {self.name}"
