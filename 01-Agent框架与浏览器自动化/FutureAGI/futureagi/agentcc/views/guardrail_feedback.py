from collections import defaultdict

import structlog
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from agentcc.models.guardrail_feedback import AgentccGuardrailFeedback
from agentcc.serializers.guardrail_feedback import AgentccGuardrailFeedbackSerializer
from tfc.utils.base_viewset import BaseModelViewSetMixinWithUserOrg
from tfc.utils.general_methods import GeneralMethods

logger = structlog.get_logger(__name__)


class AgentccGuardrailFeedbackViewSet(BaseModelViewSetMixinWithUserOrg, ModelViewSet):
    """Feedback on guardrail decisions. Org-scoped."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentccGuardrailFeedbackSerializer
    queryset = AgentccGuardrailFeedback.no_workspace_objects.all()
    _gm = GeneralMethods()

    def get_queryset(self):
        qs = super().get_queryset()
        # Optional filters
        check_name = self.request.query_params.get("check_name")
        if check_name:
            qs = qs.filter(check_name=check_name)
        feedback_type = self.request.query_params.get("feedback")
        if feedback_type:
            qs = qs.filter(feedback=feedback_type)
        request_log_id = self.request.query_params.get("request_log_id")
        if request_log_id:
            qs = qs.filter(request_log_id=request_log_id)
        return qs

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = AgentccGuardrailFeedbackSerializer(queryset, many=True)
            return self._gm.success_response(serializer.data)
        except Exception as e:
            logger.exception("guardrail_feedback_list_error", error=str(e))
            return self._gm.bad_request(str(e))

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            return self._gm.success_response(
                AgentccGuardrailFeedbackSerializer(instance).data
            )
        except Exception as e:
            logger.exception("guardrail_feedback_retrieve_error", error=str(e))
            return self._gm.not_found("Feedback not found")

    def create(self, request, *args, **kwargs):
        try:
            serializer = AgentccGuardrailFeedbackSerializer(data=request.data)
            if not serializer.is_valid():
                return self._gm.bad_request(serializer.errors)

            org = getattr(request, "organization", None)
            if org is None:
                return self._gm.bad_request("Organization context is required")

            # Validate request_log belongs to same org
            request_log = serializer.validated_data.get("request_log")
            if request_log and request_log.organization_id != org.id:
                return self._gm.bad_request(
                    "Request log does not belong to your organization"
                )

            feedback = serializer.save(
                organization=org,
                created_by=request.user,
            )
            return self._gm.success_response(
                AgentccGuardrailFeedbackSerializer(feedback).data
            )
        except Exception as e:
            logger.exception("guardrail_feedback_create_error", error=str(e))
            return self._gm.bad_request(str(e))

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.deleted = True
            instance.save(update_fields=["deleted", "updated_at"])
            return self._gm.success_response({"deleted": True})
        except Exception as e:
            logger.exception("guardrail_feedback_delete_error", error=str(e))
            return self._gm.bad_request(str(e))

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Aggregate feedback stats per check_name."""
        try:
            qs = self.get_queryset()
            feedback_data = qs.values("check_name", "feedback")

            stats = defaultdict(
                lambda: {
                    "total": 0,
                    "correct": 0,
                    "false_positive": 0,
                    "false_negative": 0,
                    "unsure": 0,
                }
            )

            for row in feedback_data:
                name = row["check_name"]
                fb = row["feedback"]
                stats[name]["total"] += 1
                if fb in stats[name]:
                    stats[name][fb] += 1

            result = []
            for name, data in sorted(stats.items()):
                total = data["total"]
                result.append(
                    {
                        "check_name": name,
                        "total_feedback": total,
                        "correct_count": data["correct"],
                        "correct_rate": (
                            round(data["correct"] / total * 100, 2)
                            if total > 0
                            else 0.0
                        ),
                        "false_positive_count": data["false_positive"],
                        "false_positive_rate": (
                            round(data["false_positive"] / total * 100, 2)
                            if total > 0
                            else 0.0
                        ),
                        "false_negative_count": data["false_negative"],
                        "false_negative_rate": (
                            round(data["false_negative"] / total * 100, 2)
                            if total > 0
                            else 0.0
                        ),
                        "unsure_count": data["unsure"],
                    }
                )

            return self._gm.success_response(result)
        except Exception as e:
            logger.exception("guardrail_feedback_summary_error", error=str(e))
            return self._gm.bad_request(str(e))
