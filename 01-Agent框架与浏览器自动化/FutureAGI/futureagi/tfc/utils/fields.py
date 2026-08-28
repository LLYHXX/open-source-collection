from django.db import models

from accounts.models.workspace import Workspace
from tfc.middleware.workspace_context import (
    get_current_organization,
    get_current_workspace,
)


class AutoWorkspaceField(models.ForeignKey):
    """
    A ForeignKey field that automatically assigns the workspace from thread-local
    context when creating new instances.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("null", True)
        kwargs.setdefault("blank", True)
        kwargs.setdefault("to", Workspace)
        kwargs.setdefault("on_delete", models.CASCADE)
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if add and not getattr(model_instance, self.attname):
            current_workspace = get_current_workspace()
            if current_workspace:
                setattr(model_instance, self.attname, current_workspace)
        return super().pre_save(model_instance, add)


class AutoOrganizationField(models.ForeignKey):
    """
    A ForeignKey field that automatically assigns the organization from thread-local
    context when creating new instances.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("null", True)
        kwargs.setdefault("blank", True)
        kwargs.setdefault("to", "accounts.Organization")
        kwargs.setdefault("on_delete", models.CASCADE)
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if add and not getattr(model_instance, self.attname):
            current_organization = get_current_organization()
            if current_organization:
                setattr(model_instance, self.attname, current_organization)
        return super().pre_save(model_instance, add)
