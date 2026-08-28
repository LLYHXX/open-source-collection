from rest_framework import serializers

from model_hub.models.tts_voices import TTSVoice


class TTSVoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TTSVoice
        fields = [
            "id",
            "name",
            "description",
            "voice_id",
            "provider",
            "model",
            "voice_type",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "voice_type"]

    def create(self, validated_data):
        validated_data["organization"] = self.context["request"].user.organization
        # Ensure voice_type is custom
        validated_data["voice_type"] = "custom"
        return super().create(validated_data)
