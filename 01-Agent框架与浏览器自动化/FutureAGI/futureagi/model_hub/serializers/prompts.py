from rest_framework import serializers

from model_hub.models.prompt import Prompt


class PromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prompt
        fields = [
            "id",
            "common_id",
            "content",
            "variables",
            "created_at",
            "updated_at",
            "is_current",
            "version",
            "used_in",
            "develop",
        ]
        read_only_fields = [
            "id",
            "common_id",
            "created_at",
            "updated_at",
            "is_current",
            "version",
        ]


class PromptListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prompt
        fields = [
            "id",
            "common_id",
            "content",
            "version",
            "is_current",
            "used_in",
            "develop",
        ]


class PromptVersionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Prompt
        fields = [
            "id",
            "version",
            "content",
            "variables",
            "created_at",
            "updated_at",
            "is_current",
        ]


class CreatePromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prompt
        fields = ["content", "variables", "used_in", "develop"]

    def create(self, validated_data):
        return Prompt.objects.create(**validated_data)


class UpdatePromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prompt
        fields = ["content", "variables", "used_in", "develop"]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
