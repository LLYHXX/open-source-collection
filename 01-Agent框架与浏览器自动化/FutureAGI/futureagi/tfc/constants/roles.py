"""
Centralized constants for roles and permissions across the application.
This file should be the single source of truth for all role-related constants.
"""

from django.db import models


class OrganizationRoles(models.TextChoices):
    OWNER = "Owner", "Owner"
    ADMIN = "Admin", "Admin"
    MEMBER = "Member", "Member"
    MEMBER_VIEW_ONLY = "Viewer", "Viewer"
    WORKSPACE_ADMIN = "workspace_admin", "Workspace Admin"
    WORKSPACE_MEMBER = "workspace_member", "Workspace Member"
    WORKSPACE_VIEWER = "workspace_viewer", "Workspace Viewer"


# Role permissions
class RolePermissions:
    # Organization roles that have global access to all workspaces
    GLOBAL_ACCESS_ROLES = [
        OrganizationRoles.OWNER,
        OrganizationRoles.ADMIN,
    ]

    # Roles that can write to workspaces
    WRITE_ACCESS_ROLES = [
        OrganizationRoles.OWNER,
        # OrganizationRoles.BILLING_ADMIN,
        OrganizationRoles.ADMIN,
        OrganizationRoles.MEMBER,
        # OrganizationRoles.WORKSPACE_OWNER,
        OrganizationRoles.WORKSPACE_ADMIN,
        OrganizationRoles.WORKSPACE_MEMBER,
    ]

    # Roles that can read from workspaces
    READ_ACCESS_ROLES = [
        OrganizationRoles.OWNER,
        # OrganizationRoles.BILLING_ADMIN,
        OrganizationRoles.ADMIN,
        OrganizationRoles.MEMBER,
        OrganizationRoles.MEMBER_VIEW_ONLY,
        # OrganizationRoles.WORKSPACE_OWNER,
        OrganizationRoles.WORKSPACE_ADMIN,
        OrganizationRoles.WORKSPACE_MEMBER,
        OrganizationRoles.WORKSPACE_VIEWER,
    ]

    # Admin roles
    ADMIN_ROLES = [
        OrganizationRoles.OWNER,
        OrganizationRoles.ADMIN,
        # OrganizationRoles.WORKSPACE_OWNER,
        OrganizationRoles.WORKSPACE_ADMIN,
    ]

    # Owner roles
    OWNER_ROLES = [
        OrganizationRoles.OWNER,
        # OrganizationRoles.WORKSPACE_OWNER,
    ]


# Mapping from organization roles to default workspace roles
class RoleMapping:
    ORG_TO_WORKSPACE_MAP = {
        OrganizationRoles.OWNER: OrganizationRoles.WORKSPACE_ADMIN,
        # OrganizationRoles.BILLING_ADMIN: OrganizationRoles.WORKSPACE_ADMIN,
        OrganizationRoles.ADMIN: OrganizationRoles.WORKSPACE_ADMIN,
        OrganizationRoles.MEMBER: OrganizationRoles.WORKSPACE_MEMBER,
        OrganizationRoles.MEMBER_VIEW_ONLY: OrganizationRoles.WORKSPACE_VIEWER,
    }

    @classmethod
    def get_workspace_role(cls, organization_role):
        """Get the default workspace role for an organization role"""
        return cls.ORG_TO_WORKSPACE_MAP.get(
            organization_role, OrganizationRoles.WORKSPACE_MEMBER
        )


# Permission constants
class Permissions:
    """Permission constants for different operations"""

    # CRUD operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

    # Special operations
    ADMIN = "admin"
    OWNER = "owner"

    # All permissions
    ALL = [CREATE, READ, UPDATE, DELETE, ADMIN, OWNER]
