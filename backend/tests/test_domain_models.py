from datetime import UTC, date, datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from project_x_backend.apps.accounts.models import User
from project_x_backend.apps.analytics.models import AnalyticsRun, IndicatorAggregate
from project_x_backend.apps.cameras.models import Camera
from project_x_backend.apps.classrooms.models import Classroom
from project_x_backend.apps.footage.models import Footage
from project_x_backend.apps.institutions.models import Institution
from project_x_backend.apps.lectures.models import Lecture
from project_x_backend.apps.processing.models import CVObservation, CVRun, ProcessingJob
from project_x_backend.apps.recommendations.models import Recommendation
from project_x_backend.apps.reports.models import LectureReport, LectureSummary
from project_x_backend.apps.timetable.models import Subject, TimetableEntry


class DomainModelTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Example College", code="EXAMPLE")
        self.classroom = Classroom.objects.create(
            institution=self.institution, code="CSE-301", capacity=45
        )
        self.camera = Camera.objects.create(
            classroom=self.classroom, identifier="CAM-1", display_name="Front"
        )
        self.subject = Subject.objects.create(
            institution=self.institution, code="CS-101", name="Computer Science"
        )
        self.teacher = User.objects.create_user(
            "TEACHER@EXAMPLE.INVALID",
            "test-password-123",
            institution=self.institution,
            role=User.Role.TEACHER,
            display_name="Test Teacher",
        )
        self.start = datetime(2026, 10, 4, 9, tzinfo=UTC)
        self.end = self.start + timedelta(hours=1)
        self.lecture = Lecture.objects.create(
            institution=self.institution,
            teacher=self.teacher,
            classroom=self.classroom,
            subject=self.subject,
            title="Recorded lecture",
            scheduled_start=self.start,
            scheduled_end=self.end,
            actual_start=self.start,
            actual_end=self.end,
            status=Lecture.Status.COMPLETED,
        )

    def test_custom_user_normalizes_email_hashes_password_and_has_role(self):
        self.assertEqual(self.teacher.email, "teacher@example.invalid")
        self.assertTrue(self.teacher.check_password("test-password-123"))
        self.assertEqual(self.teacher.role, User.Role.TEACHER)
        self.assertFalse(self.teacher.password == "test-password-123")

    def test_email_is_unique_case_insensitively_through_manager(self):
        duplicate = User(
            email="TEACHER@example.invalid",
            institution=self.institution,
            role=User.Role.TEACHER,
            display_name="Duplicate",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            duplicate.save()

    def test_classroom_room_code_is_case_insensitively_unique_per_institution(self):
        duplicate = Classroom(institution=self.institution, code="cse-301")
        with self.assertRaises(IntegrityError), transaction.atomic():
            duplicate.save()

    def test_classroom_capacity_must_be_positive(self):
        classroom = Classroom(institution=self.institution, code="ZERO", capacity=0)
        with self.assertRaises(ValidationError):
            classroom.full_clean()

    def test_camera_is_classroom_owned_and_allows_multiple_cameras(self):
        second = Camera.objects.create(
            classroom=self.classroom, identifier="CAM-2", display_name="Side"
        )
        self.assertEqual(self.classroom.cameras.count(), 2)
        self.assertEqual(second.classroom_id, self.classroom.id)

    def test_camera_identifier_is_case_insensitively_unique_across_classrooms(self):
        other_room = Classroom.objects.create(institution=self.institution, code="CSE-302")
        duplicate = Camera(classroom=other_room, identifier="cam-1", display_name="Duplicate")
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            duplicate.save()

    def test_timetable_validates_time_range_and_tenant_assignment(self):
        entry = TimetableEntry(
            institution=self.institution,
            classroom=self.classroom,
            subject=self.subject,
            teacher=self.teacher,
            weekday=0,
            start_time=time(10),
            end_time=time(9),
            valid_from=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_timetable_end_date_cannot_precede_start_date(self):
        entry = TimetableEntry(
            institution=self.institution,
            classroom=self.classroom,
            subject=self.subject,
            teacher=self.teacher,
            weekday=0,
            start_time=time(9),
            end_time=time(10),
            valid_from=date(2026, 2, 1),
            valid_to=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_timetable_rejects_references_from_another_institution(self):
        other = Institution.objects.create(name="Other College", code="OTHER")
        entry = TimetableEntry(
            institution=other,
            classroom=self.classroom,
            subject=self.subject,
            teacher=self.teacher,
            weekday=0,
            start_time=time(9),
            end_time=time(10),
            valid_from=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_completed_lecture_requires_actual_interval(self):
        lecture = Lecture(
            institution=self.institution,
            teacher=self.teacher,
            classroom=self.classroom,
            subject=self.subject,
            status=Lecture.Status.COMPLETED,
        )
        with self.assertRaises(ValidationError):
            lecture.full_clean()

    def test_footage_requires_matching_camera_and_external_storage_reference_after_storage(self):
        footage = Footage(
            lecture=self.lecture,
            camera=self.camera,
            filename="lecture.mp4",
            status=Footage.Status.STORED,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            footage.save()
        footage.status = Footage.Status.DISCOVERED
        footage.recorded_start = self.end
        footage.recorded_end = self.start
        with self.assertRaises(ValidationError):
            footage.full_clean()

    def test_footage_camera_must_belong_to_lecture_classroom(self):
        other_room = Classroom.objects.create(institution=self.institution, code="CSE-302")
        other_camera = Camera.objects.create(
            classroom=other_room, identifier="CAM-OTHER", display_name="Other room"
        )
        footage = Footage(lecture=self.lecture, camera=other_camera, filename="wrong-room.mp4")
        with self.assertRaises(ValidationError):
            footage.full_clean()

    def test_processing_jobs_allow_multiple_jobs_per_footage_and_bound_attempts(self):
        footage = Footage.objects.create(
            lecture=self.lecture, camera=self.camera, filename="segment.mp4"
        )
        first = ProcessingJob.objects.create(footage=footage, idempotency_key="request-1")
        second = ProcessingJob.objects.create(footage=footage, idempotency_key="request-2")
        self.assertEqual(footage.processing_jobs.count(), 2)
        self.assertEqual(first.status, ProcessingJob.Status.PENDING)
        self.assertEqual(second.status, ProcessingJob.Status.PENDING)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProcessingJob.objects.create(
                footage=footage, idempotency_key="request-3", max_attempts=1, attempt_count=2
            )

    def test_processing_job_idempotency_key_is_unique_per_footage(self):
        footage = Footage.objects.create(
            lecture=self.lecture, camera=self.camera, filename="idempotent.mp4"
        )
        ProcessingJob.objects.create(footage=footage, idempotency_key="same-request")
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProcessingJob.objects.create(footage=footage, idempotency_key="same-request")

    def test_cv_observations_are_run_scoped_and_validate_window_and_confidence(self):
        footage = Footage.objects.create(
            lecture=self.lecture, camera=self.camera, filename="observed.mp4"
        )
        job = ProcessingJob.objects.create(footage=footage, idempotency_key="cv")
        cv_run = CVRun.objects.create(
            processing_job=job, pipeline_version="p1", sampling_policy="sample-v1"
        )
        observation = CVObservation(
            cv_run=cv_run,
            window_start_ms=0,
            window_end_ms=1000,
            track_ref="TRACK_001",
            face_visible=True,
            face_visibility_confidence=1.2,
        )
        with self.assertRaises(ValidationError):
            observation.full_clean()
        valid = CVObservation.objects.create(
            cv_run=cv_run, window_start_ms=0, window_end_ms=1000, track_ref="TRACK_001"
        )
        self.assertEqual(valid.cv_run_id, cv_run.id)

    def test_analytics_run_must_use_cv_output_from_its_processing_job(self):
        footage = Footage.objects.create(
            lecture=self.lecture, camera=self.camera, filename="analytics.mp4"
        )
        job = ProcessingJob.objects.create(footage=footage, idempotency_key="analytics")
        other_job = ProcessingJob.objects.create(footage=footage, idempotency_key="other")
        cv_run = CVRun.objects.create(
            processing_job=other_job, pipeline_version="p1", sampling_policy="sample-v1"
        )
        analytics_run = AnalyticsRun(
            lecture=self.lecture,
            processing_job=job,
            input_cv_run=cv_run,
            rule_set_version="rules-v1",
        )
        with self.assertRaises(ValidationError):
            analytics_run.full_clean()

    def test_indicator_has_window_quality_and_versioned_run_relationship(self):
        footage = Footage.objects.create(
            lecture=self.lecture, camera=self.camera, filename="metric.mp4"
        )
        job = ProcessingJob.objects.create(footage=footage, idempotency_key="metric")
        cv_run = CVRun.objects.create(
            processing_job=job, pipeline_version="p1", sampling_policy="sample-v1"
        )
        run = AnalyticsRun.objects.create(
            lecture=self.lecture,
            processing_job=job,
            input_cv_run=cv_run,
            rule_set_version="rules-v1",
        )
        aggregate = IndicatorAggregate.objects.create(
            analytics_run=run,
            indicator_code=IndicatorAggregate.IndicatorCode.ATTENTION,
            window_start=self.start,
            window_end=self.end,
            value="0.75",
            unit="unspecified",
        )
        self.assertEqual(aggregate.analytics_run.lecture_id, self.lecture.id)

    def test_summary_report_and_recommendation_preserve_analytics_provenance(self):
        footage = Footage.objects.create(
            lecture=self.lecture, camera=self.camera, filename="report.mp4"
        )
        job = ProcessingJob.objects.create(footage=footage, idempotency_key="report")
        cv_run = CVRun.objects.create(
            processing_job=job, pipeline_version="p1", sampling_policy="sample-v1"
        )
        run = AnalyticsRun.objects.create(
            lecture=self.lecture,
            processing_job=job,
            input_cv_run=cv_run,
            rule_set_version="rules-v1",
        )
        summary = LectureSummary.objects.create(lecture=self.lecture, analytics_run=run)
        self.assertEqual(summary.analytics_run_id, run.id)
        with self.assertRaises(IntegrityError), transaction.atomic():
            LectureSummary.objects.create(lecture=self.lecture, analytics_run=run)
        report = LectureReport.objects.create(lecture=self.lecture, analytics_run=run)
        recommendation = Recommendation.objects.create(
            lecture=self.lecture,
            analytics_run=run,
            recommendation_type="PATTERN",
            rule_id="rule-1",
            observation="Example pattern",
            content="Example text",
        )
        self.assertEqual(report.analytics_run_id, recommendation.analytics_run_id)
