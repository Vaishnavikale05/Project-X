"""Root routes: infrastructure endpoints only; no business APIs yet."""

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from project_x_backend.apps.accounts.api.urls import urlpatterns as auth_urlpatterns
from project_x_backend.apps.cameras.api.urls import urlpatterns as camera_urlpatterns
from project_x_backend.apps.classrooms.api.urls import urlpatterns as classroom_urlpatterns
from project_x_backend.apps.institutions.api.urls import urlpatterns as institution_urlpatterns

urlpatterns = [
    path("api/v1/", include("project_x_backend.infrastructure.api.urls")),
    path("api/v1/auth/", include(auth_urlpatterns)),
    path("api/v1/institutions/", include(institution_urlpatterns)),
    path("api/v1/classrooms/", include(classroom_urlpatterns)),
    path("api/v1/cameras/", include(camera_urlpatterns)),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="openapi-schema"),
    path(
        "api/v1/docs/", SpectacularSwaggerView.as_view(url_name="openapi-schema"), name="api-docs"
    ),
]
