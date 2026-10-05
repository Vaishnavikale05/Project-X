"""Authentication and authorization API behavior."""

from datetime import timedelta
from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import AccessToken

from project_x_backend.apps.accounts.models import User
from project_x_backend.apps.accounts.permissions import IsAdminRole, IsTeacherRole
from project_x_backend.apps.institutions.models import Institution
from project_x_backend.infrastructure.api.exceptions import api_exception_handler


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication"
        ],
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
        "DEFAULT_THROTTLE_RATES": {"auth_login": "100/min", "auth_refresh": "100/min"},
        "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
        "EXCEPTION_HANDLER": (
            "project_x_backend.infrastructure.api.exceptions.api_exception_handler"
        ),
    }
)
class AuthenticationApiTests(TestCase):
    password = "Secur3-College-Auth-Passphrase!"

    @classmethod
    def setUpTestData(cls):
        cls.institution = Institution.objects.create(name="Auth Test College", code="AUTH-T")
        cls.admin = User.objects.create_user(
            email="admin@example.invalid",
            password=cls.password,
            display_name="Auth Admin",
            institution=cls.institution,
            role=User.Role.ADMIN,
        )
        cls.teacher = User.objects.create_user(
            email="teacher@example.invalid",
            password=cls.password,
            display_name="Auth Teacher",
            institution=cls.institution,
            role=User.Role.TEACHER,
        )

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def csrf_token(self):
        response = self.client.get("/api/v1/auth/csrf/")
        self.assertEqual(response.status_code, 200)
        return response.json()["csrf_token"]

    def login(self, email="admin@example.invalid", password=None):
        csrf = self.csrf_token()
        return self.client.post(
            "/api/v1/auth/login",
            {"email": email, "password": password or self.password},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )

    def test_login_is_case_insensitive_and_returns_only_safe_user_and_access_token(self):
        response = self.login("ADMIN@EXAMPLE.INVALID")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["user"]["id"], str(self.admin.id))
        self.assertEqual(body["user"]["role"], User.Role.ADMIN)
        self.assertNotIn("password", body["user"])
        self.assertNotIn("password", body)
        self.assertNotIn("refresh", body)
        self.assertTrue(body["access"])

        cookie = response.cookies["project_x_refresh"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(cookie["path"], "/api/v1/auth/")
        access_claims = AccessToken(body["access"])
        self.assertEqual(
            access_claims["exp"] - access_claims["iat"],
            int(jwt_settings.ACCESS_TOKEN_LIFETIME.total_seconds()),
        )

    def test_invalid_credentials_nonexistent_and_inactive_accounts_are_indistinguishable(self):
        self.teacher.is_active = False
        self.teacher.save(update_fields=["is_active"])

        wrong_password = self.login(password="wrong password")
        nonexistent = self.login("missing@example.invalid")
        inactive = self.login("teacher@example.invalid")

        statuses = [response.status_code for response in (wrong_password, nonexistent, inactive)]
        self.assertEqual(
            statuses,
            [401] * 3,
            [response.json() for response in (wrong_password, nonexistent, inactive)],
        )
        details = [
            response.json()["error"]["details"]
            for response in (wrong_password, nonexistent, inactive)
        ]
        self.assertEqual(details[0], details[1])
        self.assertEqual(details[1], details[2])
        self.assertEqual(details[0]["detail"], "Invalid email or password.")

    def test_malformed_login_is_a_validation_error(self):
        csrf = self.csrf_token()
        response = self.client.post(
            "/api/v1/auth/login",
            {"email": "not-an-email", "password": ""},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["message"], "Request validation failed.")

    def test_login_requires_csrf_header(self):
        self.client.get("/api/v1/auth/csrf/")
        response = self.client.post(
            "/api/v1/auth/login",
            {"email": "admin@example.invalid", "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("csrf", response.json()["error"]["details"]["detail"].lower())

    def test_me_requires_access_token_and_returns_safe_user_fields(self):
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)
        response = self.login()
        access = response.json()["access"]
        me = self.client.get("/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {access}")

        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["email"], self.admin.email)
        self.assertEqual(me.json()["role"], User.Role.ADMIN)
        self.assertEqual(me.json()["display_name"], self.admin.display_name)
        self.assertEqual(me.json()["institution_id"], str(self.institution.id))
        self.assertNotIn("password", me.json())
        self.assertNotIn("last_login", me.json())

    def test_invalid_and_expired_access_tokens_are_rejected(self):
        invalid = self.client.get("/api/v1/auth/me", HTTP_AUTHORIZATION="Bearer not-a-jwt")
        token = AccessToken.for_user(self.admin)
        token.set_exp(from_time=timezone.now(), lifetime=timedelta(seconds=-1))
        expired = self.client.get("/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {token}")

        self.assertEqual(invalid.status_code, 401)
        self.assertEqual(expired.status_code, 401)

    def test_refresh_rotates_and_blacklists_the_previous_refresh_token(self):
        login_response = self.login()
        csrf = self.csrf_token()
        old_refresh = login_response.cookies["project_x_refresh"].value
        self.client.cookies["project_x_refresh"] = old_refresh

        refreshed = self.client.post(
            "/api/v1/auth/refresh", {}, format="json", HTTP_X_CSRFTOKEN=csrf
        )
        self.assertEqual(refreshed.status_code, 200)
        new_refresh = refreshed.cookies["project_x_refresh"].value
        self.assertNotEqual(new_refresh, old_refresh)
        self.assertNotIn("refresh", refreshed.json())

        self.client.cookies["project_x_refresh"] = old_refresh
        reused = self.client.post("/api/v1/auth/refresh", {}, format="json", HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(reused.status_code, 401)

    def test_invalid_refresh_is_rejected_and_cookie_is_cleared(self):
        csrf = self.csrf_token()
        self.client.cookies["project_x_refresh"] = "invalid-refresh-token"
        response = self.client.post(
            "/api/v1/auth/refresh", {}, format="json", HTTP_X_CSRFTOKEN=csrf
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.cookies["project_x_refresh"]["max-age"], 0)

    def test_logout_revokes_refresh_cookie_and_is_idempotent(self):
        login_response = self.login()
        access = login_response.json()["access"]
        csrf = self.csrf_token()
        refresh = login_response.cookies["project_x_refresh"].value
        self.client.cookies["project_x_refresh"] = refresh

        logout = self.client.post("/api/v1/auth/logout", {}, format="json", HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(logout.status_code, 204)
        self.assertEqual(logout.cookies["project_x_refresh"]["max-age"], 0)

        self.client.cookies["project_x_refresh"] = refresh
        refresh_after_logout = self.client.post(
            "/api/v1/auth/refresh", {}, format="json", HTTP_X_CSRFTOKEN=csrf
        )
        self.assertEqual(refresh_after_logout.status_code, 401)

        # Logout revokes refresh credentials; the short-lived access JWT remains valid.
        access_after_logout = self.client.get(
            "/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {access}"
        )
        self.assertEqual(access_after_logout.status_code, 200)

    def test_logout_requires_csrf_validation(self):
        self.csrf_token()
        response = self.client.post("/api/v1/auth/logout", {}, format="json")
        self.assertEqual(response.status_code, 403)


class RolePermissionTests(TestCase):
    def setUp(self):
        institution = Institution.objects.create(name="Permission College", code="PERM-T")
        self.admin = User.objects.create_user(
            email="permission-admin@example.invalid",
            password="Secur3-College-Auth-Passphrase!",
            display_name="Permission Admin",
            institution=institution,
            role=User.Role.ADMIN,
        )
        self.teacher = User.objects.create_user(
            email="permission-teacher@example.invalid",
            password="Secur3-College-Auth-Passphrase!",
            display_name="Permission Teacher",
            institution=institution,
            role=User.Role.TEACHER,
        )

    def request_for(self, user):
        return SimpleNamespace(user=user)

    def test_admin_and_teacher_roles_are_separated(self):
        view = SimpleNamespace()
        self.assertTrue(IsAdminRole().has_permission(self.request_for(self.admin), view))
        self.assertFalse(IsAdminRole().has_permission(self.request_for(self.teacher), view))
        self.assertTrue(IsTeacherRole().has_permission(self.request_for(self.teacher), view))
        self.assertFalse(IsTeacherRole().has_permission(self.request_for(self.admin), view))
        self.assertFalse(IsAdminRole().has_permission(self.request_for(AnonymousUser()), view))

    def test_user_creation_enforces_django_password_validators(self):
        with self.assertRaises(ValidationError):
            User.objects.create_user(
                email="weak-password@example.invalid",
                password="short",
                display_name="Weak Password",
                institution=self.admin.institution,
                role=User.Role.TEACHER,
            )

    def test_exception_logs_do_not_include_sensitive_message_contents(self):
        request = SimpleNamespace(request_id="auth-test")
        sensitive = "password=secret-example token=eyJhbGciOiJIUzI1NiJ9"
        with self.assertLogs(
            "project_x_backend.infrastructure.api.exceptions", level="ERROR"
        ) as captured:
            api_exception_handler(RuntimeError(sensitive), {"request": request})
        log_output = "\n".join(captured.output)
        self.assertNotIn("secret-example", log_output)
        self.assertNotIn("eyJhbGci", log_output)
        self.assertEqual(captured.records[0].exception_type, "RuntimeError")
