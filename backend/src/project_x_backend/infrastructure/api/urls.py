"""Version 1 infrastructure routes. Business modules add routes in later phases."""

from django.urls import path

from .health import HealthView

urlpatterns = [path("health", HealthView.as_view(), name="api-health")]
