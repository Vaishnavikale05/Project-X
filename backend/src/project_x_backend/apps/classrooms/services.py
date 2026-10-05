from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from project_x_backend.apps.classrooms.models import Classroom
from project_x_backend.apps.institutions.models import Institution
from project_x_backend.apps.institutions.policies import assert_infrastructure_admin
from project_x_backend.apps.operations.services import write_resource_audit
from project_x_backend.infrastructure.api.exceptions import ResourceConflict


def _validate_and_save(instance):
    try:
        instance.full_clean()
        with transaction.atomic():
            instance.save()
    except DjangoValidationError as exc:
        raise ValidationError(getattr(exc, "message_dict", exc.messages)) from exc
    except IntegrityError as exc:
        raise ResourceConflict("Room code must be unique within the institution.") from exc


@transaction.atomic
def create_classroom(*, actor, values, request_id):
    institution = get_object_or_404(
        Institution.objects.select_for_update(), pk=actor.institution_id
    )
    assert_infrastructure_admin(actor, institution.pk)
    if not institution.is_active:
        raise ResourceConflict("An inactive institution cannot receive new classrooms.")
    classroom = Classroom(institution=institution, **values)
    _validate_and_save(classroom)
    write_resource_audit(
        actor=actor,
        resource=classroom,
        action="classroom.created",
        request_id=request_id,
        changed_fields=values.keys(),
    )
    return classroom


@transaction.atomic
def update_classroom(*, actor, classroom_id, changes, request_id):
    institution = get_object_or_404(
        Institution.objects.select_for_update(), pk=actor.institution_id
    )
    assert_infrastructure_admin(actor, institution.pk)
    classroom = get_object_or_404(
        Classroom.objects.select_for_update().filter(institution=institution), pk=classroom_id
    )
    if changes.get("is_active") is False and classroom.is_active:
        if classroom.cameras.filter(status="ACTIVE").exists():
            raise ResourceConflict("Deactivate active cameras before deactivating the classroom.")
    if changes.get("is_active") is True and not institution.is_active:
        raise ResourceConflict("A classroom cannot be activated while its institution is inactive.")

    for field, value in changes.items():
        setattr(classroom, field, value)
    _validate_and_save(classroom)
    write_resource_audit(
        actor=actor,
        resource=classroom,
        action="classroom.deactivated"
        if changes.get("is_active") is False
        else "classroom.updated",
        request_id=request_id,
        changed_fields=changes.keys(),
    )
    return classroom
