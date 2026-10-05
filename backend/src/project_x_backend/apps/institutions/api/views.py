from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from project_x_backend.apps.accounts.permissions import IsAdminOrTeacherRole, IsAdminRole
from project_x_backend.apps.institutions.api.serializers import InstitutionSerializer
from project_x_backend.apps.institutions.models import Institution
from project_x_backend.apps.institutions.policies import institutions_for
from project_x_backend.apps.institutions.services import update_institution
from project_x_backend.infrastructure.api.pagination import ResourcePagination
from project_x_backend.infrastructure.api.serializers import ApiErrorSerializer


class InstitutionListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrTeacherRole]

    @extend_schema(responses={200: InstitutionSerializer(many=True)})
    def get(self, request):
        queryset = institutions_for(request.user)
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(code__icontains=search))
        paginator = ResourcePagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(InstitutionSerializer(page, many=True).data)

    @extend_schema(
        request=None,
        responses={403: ApiErrorSerializer},
        description=(
            "Institutions are provisioned at deployment/bootstrap time; "
            "institution-scoped admins cannot create them."
        ),
    )
    def post(self, request):
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("Institutions are provisioned outside the administrator API.")


class InstitutionDetailView(APIView):
    def get_permissions(self):
        role_permission = IsAdminRole if self.request.method == "PATCH" else IsAdminOrTeacherRole
        return [IsAuthenticated(), role_permission()]

    def get_object(self, request, pk):
        try:
            institution = institutions_for(request.user).get(pk=pk)
        except (Institution.DoesNotExist, ValueError) as exc:
            from rest_framework.exceptions import NotFound

            raise NotFound("The requested resource was not found.") from exc
        return institution

    @extend_schema(responses={200: InstitutionSerializer})
    def get(self, request, pk):
        return Response(InstitutionSerializer(self.get_object(request, pk)).data)

    @extend_schema(
        request=InstitutionSerializer,
        responses={
            200: InstitutionSerializer,
            400: ApiErrorSerializer,
            403: ApiErrorSerializer,
            404: ApiErrorSerializer,
            409: ApiErrorSerializer,
        },
    )
    def patch(self, request, pk):
        instance = self.get_object(request, pk)
        serializer = InstitutionSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        institution = update_institution(
            actor=request.user,
            changes=serializer.validated_data,
            request_id=getattr(request, "request_id", None),
        )
        return Response(InstitutionSerializer(institution).data, status=status.HTTP_200_OK)
