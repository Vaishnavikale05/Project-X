from rest_framework.exceptions import NotFound, PermissionDenied

from project_x_backend.apps.accounts.models import User


def assert_institution_member(user: User, institution_id) -> None:
    if not user.is_authenticated:
        raise PermissionDenied
    if str(user.institution_id) != str(institution_id):
        raise NotFound("The requested resource was not found.")


def institutions_for(user):
    from project_x_backend.apps.institutions.models import Institution

    return Institution.objects.filter(pk=user.institution_id)


def classrooms_for(user):
    from project_x_backend.apps.classrooms.models import Classroom

    return Classroom.objects.filter(institution_id=user.institution_id)


def cameras_for(user):
    from project_x_backend.apps.cameras.models import Camera

    return Camera.objects.filter(classroom__institution_id=user.institution_id)


def assert_infrastructure_admin(user: User, institution_id) -> None:
    assert_institution_member(user, institution_id)
    if user.role != User.Role.ADMIN:
        raise PermissionDenied("Only an institution administrator can change infrastructure.")
