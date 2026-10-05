import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower


class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(
        "institutions.Institution", on_delete=models.PROTECT, related_name="subjects"
    )
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=160)
    department = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["institution", "code"]
        constraints = [
            models.UniqueConstraint(
                F("institution"), Lower("code"), name="subject_inst_code_ci_uniq"
            )
        ]
        indexes = [
            models.Index(fields=["institution", "is_active"], name="subject_institution_active_idx")
        ]

    def __str__(self) -> str:
        return f"{self.code}: {self.name}"


class TimetableEntry(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(
        "institutions.Institution", on_delete=models.PROTECT, related_name="timetable_entries"
    )
    classroom = models.ForeignKey(
        "classrooms.Classroom", on_delete=models.PROTECT, related_name="timetable_entries"
    )
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="timetable_entries")
    teacher = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="timetable_entries"
    )
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["weekday", "start_time"]
        constraints = [
            models.CheckConstraint(
                condition=Q(start_time__lt=models.F("end_time")), name="timetable_start_before_end"
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=models.F("valid_from")),
                name="timetable_valid_dates_ordered",
            ),
            models.CheckConstraint(
                condition=Q(weekday__gte=0, weekday__lte=6), name="timetable_weekday_range"
            ),
        ]
        indexes = [
            models.Index(
                fields=["institution", "weekday", "start_time"],
                name="timetable_institution_day_idx",
            ),
            models.Index(
                fields=["classroom", "weekday", "start_time"], name="timetable_room_day_idx"
            ),
            models.Index(
                fields=["teacher", "weekday", "start_time"], name="timetable_teacher_day_idx"
            ),
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
                errors[field] = "Must belong to the same institution."
        if self.teacher and self.teacher.role != self.teacher.Role.TEACHER:
            errors["teacher"] = "Timetable teacher must have the TEACHER role."
        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"{self.get_weekday_display()} {self.start_time:%H:%M} {self.classroom}"
