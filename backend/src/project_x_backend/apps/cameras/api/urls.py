from django.urls import path

from project_x_backend.apps.cameras.api.views import CameraDetailView, CameraListCreateView

urlpatterns = [
    path("", CameraListCreateView.as_view(), name="camera-list"),
    path("<uuid:pk>/", CameraDetailView.as_view(), name="camera-detail"),
]
