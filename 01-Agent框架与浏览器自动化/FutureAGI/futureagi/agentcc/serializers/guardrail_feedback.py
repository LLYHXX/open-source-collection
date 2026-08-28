from rest_framework import serializers

from agentcc.models.guardrail_feedback import AgentccGuardrailFeedback


class AgentccGuardrailFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentccGuardrailFeedback
        fields = [
            "id",
            "organization",
            "request_log",
            "check_name",
            "feedback",
            "comment",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def validate_feedback(self, value):
        valid = [c[0] for c in AgentccGuardrailFeedback.FEEDBACK_CHOICES]
        if value not in valid:
            raise serializers.ValidationError(
                f"feedback must be one of: {', '.join(valid)}"
            )
        return value
