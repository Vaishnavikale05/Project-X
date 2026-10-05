"""Reusable role permissions for DRF views and object policies."""

from rest_framework.permissions import BasePermission


class HasAnyRole(BasePermission):
    allowed_roles: frozenset[str] = frozenset()

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and getattr(user, "role", None) in self.allowed_roles
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsAdminRole(HasAnyRole):
    allowed_roles = frozenset({"ADMIN"})


class IsTeacherRole(HasAnyRole):
    allowed_roles = frozenset({"TEACHER"})


class IsAdminOrTeacherRole(HasAnyRole):
    allowed_roles = frozenset({"ADMIN", "TEACHER"})
