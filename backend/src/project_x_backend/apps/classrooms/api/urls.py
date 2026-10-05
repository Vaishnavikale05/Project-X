from django.urls import path

from project_x_backend.apps.classrooms.api.views import ClassroomDetailView, ClassroomListCreateView

urlpatterns = [
    path("", ClassroomListCreateView.as_view(), name="classroom-list"),
    path("<uuid:pk>/", ClassroomDetailView.as_view(), name="classroom-detail"),
]
