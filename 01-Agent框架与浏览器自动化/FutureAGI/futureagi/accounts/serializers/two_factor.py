from rest_framework import serializers


class TwoFactorStatusSerializer(serializers.Serializer):
    two_factor_enabled = serializers.BooleanField()
    methods = serializers.DictField()
    recovery_codes_remaining = serializers.IntegerField(allow_null=True)


class TOTPConfirmSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=6, max_length=6)


class TwoFactorVerifySerializer(serializers.Serializer):
    challenge_token = serializers.UUIDField()
    code = serializers.CharField(min_length=6, max_length=10)


class TwoFactorVerifyPasskeySerializer(serializers.Serializer):
    challenge_token = serializers.UUIDField()
    credential = serializers.JSONField()


class TwoFactorChallengeTokenSerializer(serializers.Serializer):
    challenge_token = serializers.UUIDField()


class PasskeyRegisterVerifySerializer(serializers.Serializer):
    credential = serializers.JSONField()
    name = serializers.CharField(max_length=255, required=False, default="")


class PasskeyRenameSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)


class TOTPDisableSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=6, max_length=10)


class RecoveryCodesRegenerateSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=6, max_length=10, required=False)
    password = serializers.CharField(required=False)


class OrgTwoFactorPolicySerializer(serializers.Serializer):
    require_2fa = serializers.BooleanField()
    require_2fa_grace_period_days = serializers.IntegerField(
        min_value=1, max_value=30, required=False
    )


class WebAuthnCredentialSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    created_at = serializers.DateTimeField()
    last_used_at = serializers.DateTimeField(allow_null=True)
