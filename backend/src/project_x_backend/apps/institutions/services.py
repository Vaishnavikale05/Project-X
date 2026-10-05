from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

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
        raise ResourceConflict("Institution code must be unique.") from exc


@transaction.atomic
def update_institution(*, actor, changes, request_id):
    institution = get_object_or_404(
        Institution.objects.select_for_update(), pk=actor.institution_id
    )
    assert_infrastructure_admin(actor, institution.pk)

    if changes.get("is_active") is False and institution.is_active:
        if institution.classrooms.filter(is_active=True).exists():
            raise ResourceConflict(
                "Deactivate active classrooms before deactivating the institution."
            )

    changed_fields = sorted(changes)
    for field, value in changes.items():
        setattr(institution, field, value)
    _validate_and_save(institution)
    write_resource_audit(
        actor=actor,
        resource=institution,
        action="institution.updated",
        request_id=request_id,
        changed_fields=changed_fields,
    )
    return institution
