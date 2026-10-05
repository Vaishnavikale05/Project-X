from uuid import UUID

from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from project_x_backend.apps.accounts.permissions import IsAdminOrTeacherRole, IsAdminRole
from project_x_backend.apps.cameras.api.serializers import (
    CameraReadSerializer,
    CameraWriteSerializer,
)
from project_x_backend.apps.cameras.models import Camera
from project_x_backend.apps.cameras.services import create_camera, update_camera
from project_x_backend.apps.institutions.policies import cameras_for
from project_x_backend.infrastructure.api.pagination import ResourcePagination
from project_x_backend.infrastructure.api.serializers import ApiErrorSerializer


def _visible_cameras(user):
    return cameras_for(user).select_related("classroom")


def _optional_uuid(request, parameter):
    value = request.query_params.get(parameter)
    if value is None:
        return None
    try:
        return UUID(value)
    except ValueError as exc:
        raise ValidationError({parameter: "Enter a valid UUID."}) from exc


class CameraListCreateView(APIView):
    def get_permissions(self):
        role_permission = IsAdminRole if self.request.method == "POST" else IsAdminOrTeacherRole
        return [IsAuthenticated(), role_permission()]

    @extend_schema(responses={200: CameraReadSerializer(many=True)})
    def get(self, request):
        queryset = _visible_cameras(request.user)
        institution_id = _optional_uuid(request, "institution_id")
        if institution_id and institution_id != request.user.institution_id:
            raise PermissionDenied("Infrastructure access is limited to your institution.")
        classroom_id = _optional_uuid(request, "classroom_id")
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)
        status_filter = request.query_params.get("status")
        if status_filter:
            if status_filter not in Camera.Status.values:
                raise ValidationError({"status": "Choose ACTIVE or INACTIVE."})
            queryset = queryset.filter(status=status_filter)
        source_type = request.query_params.get("source_type")
        if source_type:
            if source_type not in Camera.SourceType.values:
                raise ValidationError({"source_type": "Choose LOCAL_FILE."})
            queryset = queryset.filter(source_type=source_type)
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(identifier__icontains=search) | Q(display_name__icontains=search)
            )
        paginator = ResourcePagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(CameraReadSerializer(page, many=True).data)

    @extend_schema(
        request=CameraWriteSerializer,
        responses={
            201: CameraReadSerializer,
            400: ApiErrorSerializer,
            401: ApiErrorSerializer,
            403: ApiErrorSerializer,
            409: ApiErrorSerializer,
        },
    )
    def post(self, request):
        serializer = CameraWriteSerializer(
            data=request.data, context={"institution_id": request.user.institution_id}
        )
        serializer.is_valid(raise_exception=True)
        camera = create_camera(
            actor=request.user,
            values=serializer.validated_data,
            request_id=getattr(request, "request_id", None),
        )
        camera = Camera.objects.select_related("classroom").get(pk=camera.pk)
        return Response(CameraReadSerializer(camera).data, status=status.HTTP_201_CREATED)


class CameraDetailView(APIView):
    def get_permissions(self):
        role_permission = IsAdminRole if self.request.method == "PATCH" else IsAdminOrTeacherRole
        return [IsAuthenticated(), role_permission()]

    def get_object(self, request, pk):
        try:
            return _visible_cameras(request.user).get(pk=pk)
        except (Camera.DoesNotExist, ValueError) as exc:
            raise NotFound("The requested resource was not found.") from exc

    @extend_schema(responses={200: CameraReadSerializer})
    def get(self, request, pk):
        return Response(CameraReadSerializer(self.get_object(request, pk)).data)

    @extend_schema(
        request=CameraWriteSerializer,
        responses={
            200: CameraReadSerializer,
            400: ApiErrorSerializer,
            401: ApiErrorSerializer,
            403: ApiErrorSerializer,
            404: ApiErrorSerializer,
            409: ApiErrorSerializer,
        },
    )
    def patch(self, request, pk):
        camera = self.get_object(request, pk)
        serializer = CameraWriteSerializer(
            camera,
            data=request.data,
            partial=True,
            context={"institution_id": request.user.institution_id},
        )
        serializer.is_valid(raise_exception=True)
        camera = update_camera(
            actor=request.user,
            camera_id=camera.pk,
            changes=serializer.validated_data,
            request_id=getattr(request, "request_id", None),
        )
        camera = Camera.objects.select_related("classroom").get(pk=camera.pk)
        return Response(CameraReadSerializer(camera).data)
