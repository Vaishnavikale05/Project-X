import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class Lecture(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(
        "institutions.Institution", on_delete=models.PROTECT, related_name="lectures"
    )
    timetable_entry = models.ForeignKey(
        "timetable.TimetableEntry",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="lectures",
    )
    teacher = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="lectures")
    classroom = models.ForeignKey(
        "classrooms.Classroom", on_delete=models.PROTECT, related_name="lectures"
    )
    subject = models.ForeignKey(
        "timetable.Subject", on_delete=models.PROTECT, related_name="lectures"
    )
    title = models.CharField(max_length=200, blank=True)
    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SCHEDULED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_start", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(scheduled_start__isnull=True, scheduled_end__isnull=True)
                    | Q(
                        scheduled_start__isnull=False,
                        scheduled_end__isnull=False,
                        scheduled_start__lt=F("scheduled_end"),
                    )
                ),
                name="lecture_scheduled_interval_valid",
            ),
            models.CheckConstraint(
                condition=(
                    Q(actual_start__isnull=True, actual_end__isnull=True)
                    | Q(
                        actual_start__isnull=False,
                        actual_end__isnull=False,
                        actual_start__lt=F("actual_end"),
                    )
                ),
                name="lecture_actual_interval_valid",
            ),
            models.CheckConstraint(
                condition=~Q(status="ACTIVE") | Q(actual_start__isnull=False),
                name="lecture_active_has_start",
            ),
            models.CheckConstraint(
                condition=~Q(status="COMPLETED")
                | Q(actual_start__isnull=False, actual_end__isnull=False),
                name="lecture_completed_has_interval",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["SCHEDULED", "ACTIVE", "COMPLETED", "CANCELLED"]),
                name="lecture_status_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["institution", "status", "scheduled_start"],
                name="lecture_institution_status_idx",
            ),
            models.Index(fields=["teacher", "actual_start"], name="lecture_teacher_actual_idx"),
            models.Index(fields=["classroom", "actual_start"], name="lecture_room_actual_idx"),
        ]

    def clean(self):
        super().clean()
        errors = {}
        for field, obj in (
            ("classroom", self.classroom),
            ("subject", self.subject),
            ("teacher", self.teacher),
        ):
            if obj and self.institution_id and obj.institution_id != self.institution_id:
                errors[field] = "Must belong to the lecture institution."
        if self.teacher and self.teacher.role != self.teacher.Role.TEACHER:
            errors["teacher"] = "Lecture teacher must have the TEACHER role."
        if self.timetable_entry:
            entry = self.timetable_entry
            if (entry.institution_id, entry.classroom_id, entry.subject_id, entry.teacher_id) != (
                self.institution_id,
                self.classroom_id,
                self.subject_id,
                self.teacher_id,
            ):
                errors["timetable_entry"] = "Timetable assignment must match the lecture context."
        if (
            self.scheduled_start
            and self.scheduled_end
            and self.scheduled_start >= self.scheduled_end
        ):
            errors["scheduled_end"] = "Must be after scheduled start."
        if bool(self.scheduled_start) != bool(self.scheduled_end):
            errors["scheduled_end"] = "Scheduled start and end must be provided together."
        if self.actual_start and self.actual_end and self.actual_start >= self.actual_end:
            errors["actual_end"] = "Must be after actual start."
        if bool(self.actual_start) != bool(self.actual_end) and self.status != self.Status.ACTIVE:
            errors["actual_end"] = (
                "Actual start and end must be provided together unless the lecture is active."
            )
        if self.status == self.Status.ACTIVE and not self.actual_start:
            errors["actual_start"] = "An active lecture must have an actual start time."
        if self.status == self.Status.COMPLETED and not (self.actual_start and self.actual_end):
            errors["actual_end"] = "A completed lecture must have actual start and end times."
        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return self.title or f"{self.subject} — {self.scheduled_start or self.created_at:%Y-%m-%d}"
