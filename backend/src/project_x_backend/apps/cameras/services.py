from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from project_x_backend.apps.cameras.models import Camera
from project_x_backend.apps.classrooms.models import Classroom
from project_x_backend.apps.institutions.models import Institution
from project_x_backend.apps.institutions.policies import assert_infrastructure_admin
from project_x_backend.apps.operations.services import write_resource_audit
from project_x_backend.infrastructure.api.exceptions import ResourceConflict


def _camera_metadata(values, existing=None):
    metadata = dict(existing or {})
    for key in ("resolution", "frame_rate", "description"):
        if key not in values:
            continue
        value = values[key]
        if value in (None, ""):
            metadata.pop(key, None)
        else:
            metadata[key] = float(value) if key == "frame_rate" else value
    return metadata


def _validate_and_save(camera):
    try:
        camera.full_clean()
        with transaction.atomic():
            camera.save()
    except DjangoValidationError as exc:
        raise ValidationError(getattr(exc, "message_dict", exc.messages)) from exc
    except IntegrityError as exc:
        raise ResourceConflict("Camera code must be globally unique.") from exc


@transaction.atomic
def create_camera(*, actor, values, request_id):
    institution = get_object_or_404(
        Institution.objects.select_for_update(), pk=actor.institution_id
    )
    assert_infrastructure_admin(actor, institution.pk)
    classroom = get_object_or_404(
        Classroom.objects.select_for_update().filter(institution=institution),
        pk=values["classroom_id"],
    )
    if not institution.is_active or not classroom.is_active:
        raise ResourceConflict(
            "A camera can only be registered in an active classroom and institution."
        )

    values = dict(values)
    values.pop("classroom_id")
    metadata = _camera_metadata(values)
    for field in ("resolution", "frame_rate", "description"):
        values.pop(field, None)
    camera = Camera(
        classroom=classroom,
        identifier=values.pop("code"),
        metadata=metadata,
        **values,
    )
    _validate_and_save(camera)
    write_resource_audit(
        actor=actor,
        resource=camera,
        action="camera.created",
        request_id=request_id,
        changed_fields=("code", "display_name", "classroom", "source_type", "status", "metadata"),
    )
    return camera


@transaction.atomic
def update_camera(*, actor, camera_id, changes, request_id):
    institution = get_object_or_404(
        Institution.objects.select_for_update(), pk=actor.institution_id
    )
    assert_infrastructure_admin(actor, institution.pk)
    camera = get_object_or_404(
        Camera.objects.select_for_update().filter(classroom__institution=institution),
        pk=camera_id,
    )
    if changes.get("status") == Camera.Status.ACTIVE:
        classroom = get_object_or_404(Classroom.objects.select_for_update(), pk=camera.classroom_id)
        if not institution.is_active or not classroom.is_active:
            raise ResourceConflict(
                "A camera cannot be activated while its classroom or institution is inactive."
            )

    values = dict(changes)
    if "code" in values:
        camera.identifier = values.pop("code")
    camera.metadata = _camera_metadata(values, camera.metadata)
    for field in ("display_name", "source_type", "status"):
        if field in values:
            setattr(camera, field, values[field])
    _validate_and_save(camera)
    write_resource_audit(
        actor=actor,
        resource=camera,
        action="camera.deactivated"
        if changes.get("status") == Camera.Status.INACTIVE
        else "camera.updated",
        request_id=request_id,
        changed_fields=changes.keys(),
    )
    return camera
