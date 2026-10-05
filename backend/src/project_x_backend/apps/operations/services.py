from django.apps import apps
from django.db.models import Model


def write_resource_audit(
    *, actor, resource: Model, action: str, request_id: str | None, changed_fields=()
):
    """Write redacted resource audit context; never persist request payloads or values."""
    AuditEvent = apps.get_model("operations", "AuditEvent")
    if resource._meta.label_lower == "institutions.institution":
        institution = resource
    elif resource._meta.label_lower == "classrooms.classroom":
        institution = resource.institution
    elif resource._meta.label_lower == "cameras.camera":
        institution = resource.classroom.institution
    else:
        raise ValueError("Unsupported resource type for infrastructure audit.")

    return AuditEvent.objects.create(
        actor=actor,
        institution=institution,
        action=action,
        object_type=resource._meta.label,
        object_id=resource.pk,
        request_id=request_id or "",
        metadata_redacted={"changed_fields": sorted(set(changed_fields))},
    )
