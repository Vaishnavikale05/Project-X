from rest_framework.test import APIClient, APITestCase

from project_x_backend.apps.accounts.models import User
from project_x_backend.apps.cameras.models import Camera
from project_x_backend.apps.classrooms.models import Classroom
from project_x_backend.apps.institutions.models import Institution
from project_x_backend.apps.operations.models import AuditEvent


class InfrastructureApiTests(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Example College", code="EXAMPLE")
        self.other_institution = Institution.objects.create(name="Other College", code="OTHER")
        self.admin = User.objects.create_user(
            "admin@example.invalid",
            "test-password-123",
            institution=self.institution,
            role=User.Role.ADMIN,
            display_name="Example Admin",
        )
        self.teacher = User.objects.create_user(
            "teacher@example.invalid",
            "test-password-123",
            institution=self.institution,
            role=User.Role.TEACHER,
            display_name="Example Teacher",
        )
        self.other_admin = User.objects.create_user(
            "other-admin@example.invalid",
            "test-password-123",
            institution=self.other_institution,
            role=User.Role.ADMIN,
            display_name="Other Admin",
        )
        self.classroom = Classroom.objects.create(institution=self.institution, code="CSE-300")
        self.other_classroom = Classroom.objects.create(
            institution=self.other_institution, code="CSE-300"
        )
        self.client = APIClient()

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_unauthenticated_infrastructure_requests_return_401(self):
        response = self.client.get("/api/v1/classrooms/")
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.data)

    def test_teacher_can_read_only_own_institution_and_cannot_mutate(self):
        self.authenticate(self.teacher)
        listed = self.client.get("/api/v1/classrooms/")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data["count"], 1)
        hidden = self.client.get(f"/api/v1/classrooms/{self.other_classroom.pk}/")
        self.assertEqual(hidden.status_code, 404)
        denied = self.client.post("/api/v1/classrooms/", {"code": "CSE-301"}, format="json")
        self.assertEqual(denied.status_code, 403)
        camera = Camera.objects.create(
            classroom=self.classroom, identifier="CAM-TEACHER", display_name="Front"
        )
        denied_camera = self.client.patch(
            f"/api/v1/cameras/{camera.pk}/", {"display_name": "Changed"}, format="json"
        )
        self.assertEqual(denied_camera.status_code, 403)
        camera.refresh_from_db()
        self.assertEqual(camera.display_name, "Front")

    def test_admin_cannot_read_or_mutate_another_institutions_resources(self):
        camera = Camera.objects.create(
            classroom=self.other_classroom, identifier="CAM-OTHER", display_name="Other camera"
        )
        self.authenticate(self.admin)
        for resource_url, payload in (
            (f"/api/v1/classrooms/{self.other_classroom.pk}/", {"name": "Changed"}),
            (f"/api/v1/cameras/{camera.pk}/", {"display_name": "Changed"}),
            (f"/api/v1/institutions/{self.other_institution.pk}/", {"name": "Changed"}),
        ):
            self.assertEqual(self.client.get(resource_url).status_code, 404)
            response = self.client.patch(resource_url, payload, format="json")
            self.assertEqual(response.status_code, 404)

        self.other_classroom.refresh_from_db()
        camera.refresh_from_db()
        self.other_institution.refresh_from_db()
        self.assertEqual(self.other_classroom.name, "")
        self.assertEqual(camera.display_name, "Other camera")
        self.assertEqual(self.other_institution.name, "Other College")

    def test_classroom_create_derives_institution_and_audits_safe_context(self):
        self.authenticate(self.admin)
        response = self.client.post(
            "/api/v1/classrooms/",
            {"code": "CSE-301", "capacity": 45, "institution_id": str(self.other_institution.pk)},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("institution_id", response.data["error"]["details"])

        response = self.client.post(
            "/api/v1/classrooms/", {"code": "CSE-301", "capacity": 45}, format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["institution"]["id"], str(self.institution.pk))
        event = AuditEvent.objects.get(object_id=response.data["id"])
        self.assertEqual(event.actor_id, self.admin.pk)
        self.assertEqual(event.action, "classroom.created")
        self.assertEqual(event.metadata_redacted, {"changed_fields": ["capacity", "code"]})

    def test_case_insensitive_duplicate_classroom_code_returns_conflict_validation(self):
        self.authenticate(self.admin)
        response = self.client.post("/api/v1/classrooms/", {"code": "cse-300"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("code", response.data["error"]["details"])

    def test_invalid_capacity_is_rejected_by_api_and_model(self):
        self.authenticate(self.admin)
        response = self.client.post(
            "/api/v1/classrooms/", {"code": "CSE-301", "capacity": 0}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("capacity", response.data["error"]["details"])

    def test_camera_code_is_global_case_insensitive_and_source_reference_is_not_accepted(self):
        Camera.objects.create(
            classroom=self.classroom, identifier="CAM-GLOBAL", display_name="Existing"
        )
        self.authenticate(self.admin)
        duplicate = self.client.post(
            "/api/v1/cameras/",
            {
                "classroom_id": str(self.other_classroom.pk),
                "code": "cam-global",
                "display_name": "Duplicate",
            },
            format="json",
        )
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("code", duplicate.data["error"]["details"])

        secret = self.client.post(
            "/api/v1/cameras/",
            {
                "classroom_id": str(self.classroom.pk),
                "code": "CAM-2",
                "display_name": "Front",
                "source_reference": "rtsp://user:secret@example.invalid/stream",
            },
            format="json",
        )
        self.assertEqual(secret.status_code, 400)
        self.assertFalse(Camera.objects.filter(identifier="CAM-2").exists())
        self.assertNotIn("source_reference", secret.data)

    def test_camera_cannot_be_created_in_another_institution(self):
        self.authenticate(self.admin)
        response = self.client.post(
            "/api/v1/cameras/",
            {
                "classroom_id": str(self.other_classroom.pk),
                "code": "CAM-OTHER",
                "display_name": "Other room",
                "source_type": "LOCAL_FILE",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Camera.objects.filter(identifier="CAM-OTHER").exists())

    def test_camera_create_read_update_filter_and_audit_are_persisted(self):
        self.authenticate(self.admin)
        response = self.client.post(
            "/api/v1/cameras/",
            {
                "classroom_id": str(self.classroom.pk),
                "code": "CAM-CSE-300-01",
                "display_name": "Front camera",
                "source_type": "LOCAL_FILE",
                "resolution": "1920x1080",
                "frame_rate": "25.000",
                "description": "Front wall overview",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        camera_id = response.data["id"]
        self.assertEqual(response.data["source_type"], "LOCAL_FILE")
        self.assertEqual(response.data["resolution"], "1920x1080")
        self.assertNotIn("source_reference", response.data)
        stored = Camera.objects.get(pk=camera_id)
        self.assertEqual(stored.metadata["frame_rate"], 25.0)

        filtered = self.client.get("/api/v1/cameras/", {"classroom_id": str(self.classroom.pk)})
        self.assertEqual(filtered.data["count"], 1)
        self.assertEqual(filtered.data["results"][0]["id"], camera_id)

        updated = self.client.patch(
            f"/api/v1/cameras/{camera_id}/",
            {"display_name": "Front camera updated", "status": "INACTIVE"},
            format="json",
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data["status"], "INACTIVE")
        event = AuditEvent.objects.get(object_id=camera_id, action="camera.deactivated")
        self.assertEqual(event.actor_id, self.admin.pk)
        self.assertEqual(event.metadata_redacted, {"changed_fields": ["display_name", "status"]})
        self.assertNotIn("credential", str(event.metadata_redacted).lower())

    def test_camera_detail_from_another_institution_is_concealed(self):
        camera = Camera.objects.create(
            classroom=self.other_classroom, identifier="OTHER-CAM", display_name="Other"
        )
        self.authenticate(self.admin)
        response = self.client.get(f"/api/v1/cameras/{camera.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_classroom_pagination_and_status_filter(self):
        for number in range(30):
            Classroom.objects.create(institution=self.institution, code=f"ROOM-{number:02d}")
        self.authenticate(self.admin)
        response = self.client.get("/api/v1/classrooms/", {"page_size": 1, "is_active": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 31)
        self.assertEqual(len(response.data["results"]), 1)
        oversized = self.client.get("/api/v1/classrooms/", {"page_size": 1000})
        self.assertEqual(len(oversized.data["results"]), 31)

    def test_parent_deactivation_requires_children_to_be_deactivated_first(self):
        self.authenticate(self.admin)
        camera = Camera.objects.create(
            classroom=self.classroom, identifier="CAM-300", display_name="Front"
        )
        response = self.client.patch(
            f"/api/v1/classrooms/{self.classroom.pk}/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertTrue(self.classroom.__class__.objects.get(pk=self.classroom.pk).is_active)

        response = self.client.patch(
            f"/api/v1/cameras/{camera.pk}/", {"status": Camera.Status.INACTIVE}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.patch(
            f"/api/v1/classrooms/{self.classroom.pk}/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            AuditEvent.objects.filter(
                action__in=["camera.deactivated", "classroom.deactivated"]
            ).count(),
            2,
        )

    def test_institution_context_is_readable_but_not_creatable(self):
        self.authenticate(self.admin)
        listed = self.client.get("/api/v1/institutions/")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data["count"], 1)
        forbidden = self.client.post(
            "/api/v1/institutions/", {"name": "Another College", "code": "OTHER2"}, format="json"
        )
        self.assertEqual(forbidden.status_code, 403)
        hidden = self.client.get(f"/api/v1/institutions/{self.other_institution.pk}/")
        self.assertEqual(hidden.status_code, 404)

    def test_institution_update_is_audited_and_parent_deactivation_is_blocked(self):
        self.authenticate(self.admin)
        update = self.client.patch(
            f"/api/v1/institutions/{self.institution.pk}/",
            {"name": "Updated College"},
            format="json",
        )
        self.assertEqual(update.status_code, 200)
        event = AuditEvent.objects.get(object_id=self.institution.pk)
        self.assertEqual(event.metadata_redacted, {"changed_fields": ["name"]})
        deactivate = self.client.patch(
            f"/api/v1/institutions/{self.institution.pk}/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(deactivate.status_code, 409)

    def test_teacher_cannot_update_institution_and_list_filters_are_scoped(self):
        self.authenticate(self.teacher)
        denied = self.client.patch(
            f"/api/v1/institutions/{self.institution.pk}/", {"name": "Changed"}, format="json"
        )
        self.assertEqual(denied.status_code, 403)
        filtered = self.client.get(
            "/api/v1/cameras/", {"institution_id": str(self.other_institution.pk)}
        )
        self.assertEqual(filtered.status_code, 403)
