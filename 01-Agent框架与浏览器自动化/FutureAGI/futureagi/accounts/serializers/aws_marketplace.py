from rest_framework import serializers

from accounts.models.aws_marketplace import AWSMarketplaceCustomer


class AWSMarketplaceCustomerSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    user_email = serializers.SerializerMethodField()

    def get_user_email(self, obj):
        org = obj.organization
        if not org:
            return None
        first_member = org.members.first()
        return first_member.email if first_member else None

    class Meta:
        model = AWSMarketplaceCustomer
        fields = [
            "id",
            "created_at",
            "updated_at",
            "customer_identifier",
            "customer_aws_account_id",
            "product_code",
            "subscription_status",
            "entitlements",
            "organization",
            "organization_name",
            "user_email",
            "last_entitlement_check",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
