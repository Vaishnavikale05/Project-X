"""Email authentication that preserves the account's case-insensitive identity rule."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CaseInsensitiveEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username or kwargs.get("email")
        if not email or password is None:
            return None

        user_model = get_user_model()
        user = user_model._default_manager.filter(email__iexact=email.strip()).first()
        if user is None:
            # Match the password-hasher work done for existing accounts to reduce timing leaks.
            user_model().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
