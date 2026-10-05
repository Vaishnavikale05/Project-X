"""JWT authentication endpoints. Refresh credentials remain in HttpOnly cookies."""

from django.conf import settings
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken

from project_x_backend.apps.accounts.api.serializers import (
    AccessTokenSerializer,
    CsrfTokenSerializer,
    CurrentUserSerializer,
    LoginSerializer,
    RefreshResponseSerializer,
)
from project_x_backend.infrastructure.api.serializers import ApiErrorSerializer


def set_refresh_cookie(response, token: str) -> None:
    response.set_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        value=token,
        max_age=int(jwt_settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
        httponly=True,
        secure=settings.AUTH_REFRESH_COOKIE_SECURE,
        samesite=settings.AUTH_REFRESH_COOKIE_SAMESITE,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response) -> None:
    response.delete_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        samesite=settings.AUTH_REFRESH_COOKIE_SAMESITE,
    )


class CsrfProtectedAPIView(APIView):
    """Apply Django CSRF validation to cookie-backed JWT operations."""

    def initial(self, request, *args, **kwargs):
        SessionAuthentication().enforce_csrf(request)
        return super().initial(request, *args, **kwargs)


class BearerChallengeAuthentication(BaseAuthentication):
    """Advertise Bearer challenges so credential failures correctly return 401."""

    def authenticate(self, request):
        return None

    def authenticate_header(self, request):
        return "Bearer"


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTokenView(APIView):
    """Set the CSRF cookie and return its masked value for the request header."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="authCsrfToken",
        responses={200: CsrfTokenSerializer},
        summary="Issue a CSRF token for cookie-backed authentication requests",
    )
    def get(self, request):
        return Response(CsrfTokenSerializer({"csrf_token": get_token(request)}).data)


class AuthLoginView(CsrfProtectedAPIView):
    authentication_classes = [BearerChallengeAuthentication]
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    @extend_schema(
        operation_id="authLogin",
        auth=[],
        request=LoginSerializer,
        responses={
            200: AccessTokenSerializer,
            400: ApiErrorSerializer,
            401: ApiErrorSerializer,
            429: ApiErrorSerializer,
        },
        summary="Authenticate with email and password",
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                "access": str(refresh.access_token),
                "user": CurrentUserSerializer(user).data,
            }
        )
        set_refresh_cookie(response, str(refresh))
        return response


class AuthRefreshView(CsrfProtectedAPIView):
    authentication_classes = [BearerChallengeAuthentication]
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_refresh"

    @extend_schema(
        operation_id="authRefresh",
        auth=[],
        request=None,
        responses={
            200: RefreshResponseSerializer,
            401: ApiErrorSerializer,
            429: ApiErrorSerializer,
        },
        summary="Rotate the refresh cookie and issue a new access token",
    )
    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME)
        if not raw_refresh:
            raise AuthenticationFailed("Authentication credentials are invalid or expired.")

        serializer = TokenRefreshSerializer(data={"refresh": raw_refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except (AuthenticationFailed, TokenError) as exc:
            raise AuthenticationFailed(
                "Authentication credentials are invalid or expired."
            ) from exc

        response_data = dict(serializer.validated_data)
        rotated_refresh = response_data.pop("refresh", None)
        response = Response(response_data)
        if rotated_refresh:
            set_refresh_cookie(response, rotated_refresh)
        return response

    def handle_exception(self, exc):
        response = super().handle_exception(exc)
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            clear_refresh_cookie(response)
        return response


class AuthLogoutView(CsrfProtectedAPIView):
    authentication_classes = [BearerChallengeAuthentication]
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="authLogout",
        auth=[],
        request=None,
        responses={204: None, 403: ApiErrorSerializer},
        summary="Revoke the refresh credential and clear its cookie",
    )
    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME)
        if raw_refresh:
            try:
                RefreshToken(raw_refresh).blacklist()
            except TokenError:
                # Expired, malformed, or already revoked credentials need no further action.
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


class CurrentUserView(APIView):
    @extend_schema(
        operation_id="authMe",
        responses={200: CurrentUserSerializer, 401: ApiErrorSerializer},
        summary="Return the authenticated user's safe profile",
    )
    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)
