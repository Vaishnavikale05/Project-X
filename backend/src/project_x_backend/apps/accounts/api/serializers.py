"""Authentication request/response serializers."""

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=256, trim_whitespace=False, write_only=True)

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=attrs["password"],
        )
        if user is None:
            raise AuthenticationFailed("Invalid email or password.")
        attrs["user"] = user
        return attrs


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "display_name", "role", "is_active", "institution_id")
        read_only_fields = fields


class CsrfTokenSerializer(serializers.Serializer):
    csrf_token = serializers.CharField(read_only=True)


class AccessTokenSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    user = CurrentUserSerializer(read_only=True)


class RefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
