import re

import structlog
from django.db import transaction
from django.db.models import Max
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from agentcc.models.prompt_template import AgentccPromptTemplate
from agentcc.serializers.prompt_template import (
    AgentccPromptTemplateRenderSerializer,
    AgentccPromptTemplateSerializer,
)
from tfc.utils.base_viewset import BaseModelViewSetMixinWithUserOrg
from tfc.utils.general_methods import GeneralMethods

logger = structlog.get_logger(__name__)


class AgentccPromptTemplateViewSet(BaseModelViewSetMixinWithUserOrg, ModelViewSet):
    """Prompt template management with versioning and environment promotion."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentccPromptTemplateSerializer
    queryset = AgentccPromptTemplate.no_workspace_objects.all()
    _gm = GeneralMethods()

    def get_queryset(self):
        qs = super().get_queryset()
        env = self.request.query_params.get("environment")
        if env:
            qs = qs.filter(environment=env)
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name=name)
        active_only = self.request.query_params.get("active_only")
        if active_only == "true":
            qs = qs.filter(is_active=True)
        return qs

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = AgentccPromptTemplateSerializer(queryset, many=True)
            return self._gm.success_response(serializer.data)
        except Exception as e:
            logger.exception("prompt_template_list_error", error=str(e))
            return self._gm.bad_request(str(e))

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            return self._gm.success_response(
                AgentccPromptTemplateSerializer(instance).data
            )
        except Exception as e:
            logger.exception("prompt_template_retrieve_error", error=str(e))
            return self._gm.not_found("Prompt template not found")

    def create(self, request, *args, **kwargs):
        """Create a new prompt template version."""
        try:
            serializer = AgentccPromptTemplateSerializer(data=request.data)
            if not serializer.is_valid():
                return self._gm.bad_request(serializer.errors)

            org = getattr(request, "organization", None)
            if org is None:
                return self._gm.bad_request("Organization context is required")
            name = serializer.validated_data["name"]
            env = serializer.validated_data.get("environment", "dev")

            with transaction.atomic():
                max_version = (
                    AgentccPromptTemplate.no_workspace_objects.filter(
                        organization=org, name=name, environment=env, deleted=False
                    ).aggregate(Max("version"))["version__max"]
                    or 0
                )
                next_version = max_version + 1

                # Deactivate previous versions
                AgentccPromptTemplate.no_workspace_objects.filter(
                    organization=org,
                    name=name,
                    environment=env,
                    is_active=True,
                    deleted=False,
                ).update(is_active=False)

                template = serializer.save(
                    organization=org,
                    version=next_version,
                    created_by=request.user,
                )

            return self._gm.success_response(
                AgentccPromptTemplateSerializer(template).data
            )
        except Exception as e:
            logger.exception("prompt_template_create_error", error=str(e))
            return self._gm.bad_request(str(e))

    def update(self, request, *args, **kwargs):
        """Disabled — create a new version instead."""
        return self._gm.bad_request(
            "Prompt templates are versioned. Create a new version instead."
        )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.deleted = True
            instance.save(update_fields=["deleted", "updated_at"])
            return self._gm.success_response({"deleted": True})
        except Exception as e:
            logger.exception("prompt_template_delete_error", error=str(e))
            return self._gm.bad_request(str(e))

    @action(detail=True, methods=["post"])
    def render(self, request, pk=None):
        """Render the template with provided variables."""
        try:
            instance = self.get_object()
            render_serializer = AgentccPromptTemplateRenderSerializer(data=request.data)
            if not render_serializer.is_valid():
                return self._gm.bad_request(render_serializer.errors)

            variables = render_serializer.validated_data["variables"]
            rendered = instance.template
            for key, value in variables.items():
                rendered = rendered.replace(f"{{{{{key}}}}}", str(value))

            # Check for unresolved variables
            unresolved = re.findall(r"\{\{(\w+)\}\}", rendered)

            return self._gm.success_response(
                {
                    "rendered": rendered,
                    "unresolved_variables": unresolved,
                }
            )
        except Exception as e:
            logger.exception("prompt_template_render_error", error=str(e))
            return self._gm.bad_request(str(e))

    @action(detail=True, methods=["post"])
    def promote(self, request, pk=None):
        """Promote a template to the next environment (dev → staging → prod)."""
        try:
            instance = self.get_object()
            promotion_map = {
                AgentccPromptTemplate.ENV_DEV: AgentccPromptTemplate.ENV_STAGING,
                AgentccPromptTemplate.ENV_STAGING: AgentccPromptTemplate.ENV_PROD,
            }

            next_env = promotion_map.get(instance.environment)
            if not next_env:
                return self._gm.bad_request(
                    f"Cannot promote from '{instance.environment}' — already at highest level"
                )

            org = instance.organization

            with transaction.atomic():
                max_version = (
                    AgentccPromptTemplate.no_workspace_objects.filter(
                        organization=org,
                        name=instance.name,
                        environment=next_env,
                        deleted=False,
                    ).aggregate(Max("version"))["version__max"]
                    or 0
                )

                AgentccPromptTemplate.no_workspace_objects.filter(
                    organization=org,
                    name=instance.name,
                    environment=next_env,
                    is_active=True,
                    deleted=False,
                ).update(is_active=False)

                promoted = AgentccPromptTemplate.no_workspace_objects.create(
                    organization=org,
                    name=instance.name,
                    description=instance.description,
                    version=max_version + 1,
                    template=instance.template,
                    variables=instance.variables,
                    model=instance.model,
                    environment=next_env,
                    is_active=True,
                    created_by=request.user,
                )

            return self._gm.success_response(
                AgentccPromptTemplateSerializer(promoted).data
            )
        except Exception as e:
            logger.exception("prompt_template_promote_error", error=str(e))
            return self._gm.bad_request(str(e))
