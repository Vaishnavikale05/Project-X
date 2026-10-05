"""Versioned authentication endpoints."""

from django.urls import path

from project_x_backend.apps.accounts.api.views import (
    AuthLoginView,
    AuthLogoutView,
    AuthRefreshView,
    CsrfTokenView,
    CurrentUserView,
)

urlpatterns = [
    path("csrf/", CsrfTokenView.as_view(), name="auth-csrf"),
    path("login", AuthLoginView.as_view(), name="auth-login"),
    path("refresh", AuthRefreshView.as_view(), name="auth-refresh"),
    path("logout", AuthLogoutView.as_view(), name="auth-logout"),
    path("me", CurrentUserView.as_view(), name="auth-me"),
]
