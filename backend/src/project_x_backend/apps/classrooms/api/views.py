from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from project_x_backend.apps.accounts.permissions import IsAdminOrTeacherRole, IsAdminRole
from project_x_backend.apps.classrooms.api.serializers import (
    ClassroomReadSerializer,
    ClassroomWriteSerializer,
)
from project_x_backend.apps.classrooms.models import Classroom
from project_x_backend.apps.classrooms.services import create_classroom, update_classroom
from project_x_backend.apps.institutions.policies import classrooms_for
from project_x_backend.infrastructure.api.pagination import ResourcePagination
from project_x_backend.infrastructure.api.serializers import ApiErrorSerializer


def _visible_classrooms(user):
    return classrooms_for(user).select_related("institution")


def _parse_bool(value, field):
    if value is None:
        return None
    if value.lower() in {"true", "1"}:
        return True
    if value.lower() in {"false", "0"}:
        return False
    raise ValidationError({field: "Use true or false."})


class ClassroomListCreateView(APIView):
    def get_permissions(self):
        role_permission = IsAdminRole if self.request.method == "POST" else IsAdminOrTeacherRole
        return [IsAuthenticated(), role_permission()]

    @extend_schema(responses={200: ClassroomReadSerializer(many=True)})
    def get(self, request):
        queryset = _visible_classrooms(request.user)
        institution_id = request.query_params.get("institution_id")
        if institution_id:
            if institution_id != str(request.user.institution_id):
                raise PermissionDenied("Infrastructure access is limited to your institution.")
            queryset = queryset.filter(institution_id=institution_id)
        is_active = _parse_bool(request.query_params.get("is_active"), "is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(Q(code__icontains=search) | Q(name__icontains=search))
        paginator = ResourcePagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(ClassroomReadSerializer(page, many=True).data)

    @extend_schema(
        request=ClassroomWriteSerializer,
        responses={
            201: ClassroomReadSerializer,
            400: ApiErrorSerializer,
            401: ApiErrorSerializer,
            403: ApiErrorSerializer,
            409: ApiErrorSerializer,
        },
    )
    def post(self, request):
        serializer = ClassroomWriteSerializer(
            data=request.data, context={"institution_id": request.user.institution_id}
        )
        serializer.is_valid(raise_exception=True)
        classroom = create_classroom(
            actor=request.user,
            values=serializer.validated_data,
            request_id=getattr(request, "request_id", None),
        )
        return Response(ClassroomReadSerializer(classroom).data, status=status.HTTP_201_CREATED)


class ClassroomDetailView(APIView):
    def get_permissions(self):
        role_permission = IsAdminRole if self.request.method == "PATCH" else IsAdminOrTeacherRole
        return [IsAuthenticated(), role_permission()]

    def get_object(self, request, pk):
        try:
            return _visible_classrooms(request.user).get(pk=pk)
        except (Classroom.DoesNotExist, ValueError) as exc:
            raise NotFound("The requested resource was not found.") from exc

    @extend_schema(responses={200: ClassroomReadSerializer})
    def get(self, request, pk):
        return Response(ClassroomReadSerializer(self.get_object(request, pk)).data)

    @extend_schema(
        request=ClassroomWriteSerializer,
        responses={
            200: ClassroomReadSerializer,
            400: ApiErrorSerializer,
            401: ApiErrorSerializer,
            403: ApiErrorSerializer,
            404: ApiErrorSerializer,
            409: ApiErrorSerializer,
        },
    )
    def patch(self, request, pk):
        classroom = self.get_object(request, pk)
        serializer = ClassroomWriteSerializer(
            classroom,
            data=request.data,
            partial=True,
            context={"institution_id": request.user.institution_id},
        )
        serializer.is_valid(raise_exception=True)
        classroom = update_classroom(
            actor=request.user,
            classroom_id=classroom.pk,
            changes=serializer.validated_data,
            request_id=getattr(request, "request_id", None),
        )
        return Response(ClassroomReadSerializer(classroom).data)
