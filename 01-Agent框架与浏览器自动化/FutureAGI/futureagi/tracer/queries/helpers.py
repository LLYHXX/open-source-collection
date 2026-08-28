from accounts.models.workspace import Workspace
from tracer.models.project import Project
from tracer.models.trace import Trace


def get_default_workspace_for_project(project: Project) -> Workspace:
    if not project.workspace:
        return Workspace.objects.get(
            organization=project.organization, is_default=True, is_active=True
        )
    return project.workspace


def get_workspace_with_default(obj) -> Workspace:
    """
    Gets the workspace from an object, or falls back to the default
    active workspace for the object's organization.
    """
    workspace = getattr(obj, "workspace", None)
    if not workspace:
        return Workspace.objects.get(
            organization=obj.organization, is_default=True, is_active=True
        )
    return workspace
