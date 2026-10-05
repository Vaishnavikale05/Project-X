import os
from datetime import datetime, time, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from project_x_backend.apps.accounts.models import User
from project_x_backend.apps.cameras.models import Camera
from project_x_backend.apps.classrooms.models import Classroom
from project_x_backend.apps.footage.models import Footage
from project_x_backend.apps.institutions.models import Institution
from project_x_backend.apps.lectures.models import Lecture
from project_x_backend.apps.timetable.models import Subject, TimetableEntry


class Command(BaseCommand):
    help = "Create idempotent metadata-only Project-X demo data (development only)."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo is restricted to DEBUG settings.")
        password = os.environ.get("PROJECT_X_DEMO_PASSWORD", "ProjectX-Demo-Only-Change-Me!")
        if len(password) < 12:
            raise CommandError("PROJECT_X_DEMO_PASSWORD must contain at least 12 characters.")

        today = timezone.localdate()
        institution, _ = Institution.objects.get_or_create(
            code="DEMO", defaults={"name": "Demo College", "timezone": settings.TIME_ZONE}
        )
        rooms = {}
        cameras = {}
        for code in ("CSE-301", "CSE-302"):
            rooms[code], _ = Classroom.objects.get_or_create(
                institution=institution, code=code, defaults={"name": code, "capacity": 60}
            )
            cameras[code], _ = Camera.objects.get_or_create(
                classroom=rooms[code],
                identifier=f"CAM-{code}",
                defaults={
                    "display_name": f"{code} sample camera",
                    "source_type": Camera.SourceType.LOCAL_FILE,
                },
            )

        subjects = {}
        for code, name in (("ML-101", "Machine Learning"), ("DB-101", "DBMS")):
            subjects[code], _ = Subject.objects.get_or_create(
                institution=institution, code=code, defaults={"name": name}
            )

        users = {}
        for email, role, display_name in (
            ("admin@project-x-demo.invalid", User.Role.ADMIN, "Demo Admin"),
            ("teacher@project-x-demo.invalid", User.Role.TEACHER, "Demo Teacher"),
        ):
            users[email], created = User.objects.get_or_create(
                email=email,
                defaults={"institution": institution, "role": role, "display_name": display_name},
            )
            if created:
                users[email].set_password(password)
                users[email].save(update_fields=["password", "updated_at"])

        teacher = users["teacher@project-x-demo.invalid"]
        weekday = today.weekday()
        timetable, _ = TimetableEntry.objects.get_or_create(
            institution=institution,
            classroom=rooms["CSE-301"],
            subject=subjects["ML-101"],
            teacher=teacher,
            weekday=weekday,
            start_time=time(9, 0),
            defaults={"end_time": time(10, 0), "valid_from": today - timedelta(days=30)},
        )

        start = timezone.make_aware(datetime.combine(today - timedelta(days=1), time(9, 0)))
        end = start + timedelta(hours=1)
        completed, _ = Lecture.objects.get_or_create(
            institution=institution,
            teacher=teacher,
            classroom=rooms["CSE-301"],
            subject=subjects["ML-101"],
            scheduled_start=start,
            defaults={
                "timetable_entry": timetable,
                "title": "Demo completed lecture",
                "scheduled_end": end,
                "actual_start": start,
                "actual_end": end,
                "status": Lecture.Status.COMPLETED,
            },
        )
        upcoming_start = timezone.make_aware(
            datetime.combine(today + timedelta(days=1), time(11, 0))
        )
        Lecture.objects.get_or_create(
            institution=institution,
            teacher=teacher,
            classroom=rooms["CSE-302"],
            subject=subjects["DB-101"],
            scheduled_start=upcoming_start,
            defaults={
                "title": "Demo scheduled lecture",
                "scheduled_end": upcoming_start + timedelta(hours=1),
            },
        )
        Footage.objects.get_or_create(
            lecture=completed,
            camera=cameras["CSE-301"],
            filename="demo-lecture-metadata-only.mp4",
            defaults={
                "original_filename": "demo-lecture-metadata-only.mp4",
                "storage_provider": Footage.StorageProvider.LOCAL_FILE,
                "status": Footage.Status.DISCOVERED,
            },
        )
        self.stdout.write(
            self.style.SUCCESS("Demo metadata created. No video file was created or stored.")
        )
