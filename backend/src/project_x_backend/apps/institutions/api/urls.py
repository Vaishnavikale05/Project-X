from django.urls import path

from project_x_backend.apps.institutions.api.views import InstitutionDetailView, InstitutionListView

urlpatterns = [
    path("", InstitutionListView.as_view(), name="institution-list"),
    path("<uuid:pk>/", InstitutionDetailView.as_view(), name="institution-detail"),
]
