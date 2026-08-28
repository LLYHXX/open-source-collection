from rest_framework import serializers

from agentcc.models.blocklist import AgentccBlocklist


class AgentccBlocklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentccBlocklist
        fields = [
            "id",
            "organization",
            "name",
            "description",
            "words",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "created_at",
            "updated_at",
        ]

    def validate_words(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("words must be a JSON array")
        for i, word in enumerate(value):
            if not isinstance(word, str):
                raise serializers.ValidationError(f"Word at index {i} must be a string")
        return value
