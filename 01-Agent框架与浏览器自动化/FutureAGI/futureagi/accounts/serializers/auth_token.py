from rest_framework import serializers

from accounts.models.auth_token import AuthToken


class AuthTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthToken
        fields = "__all__"
