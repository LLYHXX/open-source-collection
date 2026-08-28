"""
Multi-Organization Support Tests — Phase 1

Tests for User model methods that resolve organization access via
OrganizationMembership (primary) with User.organization FK fallback.

Covers real-world E2E scenarios:
- User belongs to multiple orgs with different roles
- User removed from an org (membership deactivated)
- User with only legacy FK (no membership row)
- Workspace access across orgs
- Role resolution per-org
"""

import pytest

from accounts.models.organization import Organization
from accounts.models.organization_membership import OrganizationMembership
from accounts.models.user import User
from accounts.models.workspace import Workspace, WorkspaceMembership
from tfc.constants.levels import Level
from tfc.constants.roles import OrganizationRoles, RoleMapping, RolePermissions
from tfc.middleware.workspace_context import (
    clear_workspace_context,
    set_workspace_context,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def org_alpha(db):
    return Organization.objects.create(name="Alpha Corp")


@pytest.fixture
def org_beta(db):
    return Organization.objects.create(name="Beta Inc")


@pytest.fixture
def org_gamma(db):
    return Organization.objects.create(name="Gamma LLC")


@pytest.fixture
def owner_user(db, org_alpha):
    """User whose primary (legacy FK) org is Alpha, role Owner."""
    clear_workspace_context()
    set_workspace_context(organization=org_alpha)
    user = User.objects.create_user(
        email="owner@alpha.com",
        password="testpass123",
        name="Owner User",
        organization=org_alpha,
        organization_role=OrganizationRoles.OWNER,
    )
    # Also create the membership row (mirrors signup flow)
    OrganizationMembership.no_workspace_objects.create(
        user=user,
        organization=org_alpha,
        role=OrganizationRoles.OWNER,
        level=Level.OWNER,
        is_active=True,
    )
    return user


@pytest.fixture
def member_user(db, org_alpha):
    """User whose primary org is Alpha, role Member."""
    clear_workspace_context()
    set_workspace_context(organization=org_alpha)
    user = User.objects.create_user(
        email="member@alpha.com",
        password="testpass123",
        name="Member User",
        organization=org_alpha,
        organization_role=OrganizationRoles.MEMBER,
    )
    OrganizationMembership.no_workspace_objects.create(
        user=user,
        organization=org_alpha,
        role=OrganizationRoles.MEMBER,
        level=Level.MEMBER,
        is_active=True,
    )
    return user


@pytest.fixture
def viewer_user(db, org_alpha):
    """User whose primary org is Alpha, role Viewer."""
    clear_workspace_context()
    set_workspace_context(organization=org_alpha)
    user = User.objects.create_user(
        email="viewer@alpha.com",
        password="testpass123",
        name="Viewer User",
        organization=org_alpha,
        organization_role=OrganizationRoles.MEMBER_VIEW_ONLY,
    )
    OrganizationMembership.no_workspace_objects.create(
        user=user,
        organization=org_alpha,
        role=OrganizationRoles.MEMBER_VIEW_ONLY,
        level=Level.VIEWER,
        is_active=True,
    )
    return user


@pytest.fixture
def legacy_user(db, org_alpha):
    """User with only the legacy FK — NO OrganizationMembership row.

    Simulates a user created before the membership model existed.
    """
    clear_workspace_context()
    set_workspace_context(organization=org_alpha)
    return User.objects.create_user(
        email="legacy@alpha.com",
        password="testpass123",
        name="Legacy User",
        organization=org_alpha,
        organization_role=OrganizationRoles.ADMIN,
    )


@pytest.fixture
def multi_org_user(db, org_alpha, org_beta, org_gamma):
    """User who is Owner in Alpha, Admin in Beta, Viewer in Gamma."""
    clear_workspace_context()
    set_workspace_context(organization=org_alpha)
    user = User.objects.create_user(
        email="multi@orgs.com",
        password="testpass123",
        name="Multi Org User",
        organization=org_alpha,
        organization_role=OrganizationRoles.OWNER,
    )
    OrganizationMembership.no_workspace_objects.create(
        user=user,
        organization=org_alpha,
        role=OrganizationRoles.OWNER,
        level=Level.OWNER,
        is_active=True,
    )
    OrganizationMembership.no_workspace_objects.create(
        user=user,
        organization=org_beta,
        role=OrganizationRoles.ADMIN,
        level=Level.ADMIN,
        is_active=True,
    )
    OrganizationMembership.no_workspace_objects.create(
        user=user,
        organization=org_gamma,
        role=OrganizationRoles.MEMBER_VIEW_ONLY,
        level=Level.VIEWER,
        is_active=True,
    )
    return user


@pytest.fixture
def ws_alpha_default(db, org_alpha, owner_user):
    clear_workspace_context()
    set_workspace_context(organization=org_alpha)
    return Workspace.objects.create(
        name="Alpha Default",
        organization=org_alpha,
        is_default=True,
        is_active=True,
        created_by=owner_user,
    )


@pytest.fixture
def ws_alpha_staging(db, org_alpha, owner_user):
    clear_workspace_context()
    set_workspace_context(organization=org_alpha)
    return Workspace.objects.create(
        name="Alpha Staging",
        organization=org_alpha,
        is_default=False,
        is_active=True,
        created_by=owner_user,
    )


@pytest.fixture
def ws_beta_default(db, org_beta, multi_org_user):
    clear_workspace_context()
    set_workspace_context(organization=org_beta)
    return Workspace.objects.create(
        name="Beta Default",
        organization=org_beta,
        is_default=True,
        is_active=True,
        created_by=multi_org_user,
    )


# ---------------------------------------------------------------------------
# Phase 1: can_access_organization
# ---------------------------------------------------------------------------


class TestCanAccessOrganization:
    """Tests for User.can_access_organization()."""

    def test_access_via_membership(self, owner_user, org_alpha):
        """User with active membership can access org."""
        assert owner_user.can_access_organization(org_alpha) is True

    def test_no_access_to_unrelated_org(self, owner_user, org_beta):
        """User without membership or FK cannot access org."""
        assert owner_user.can_access_organization(org_beta) is False

    def test_legacy_fallback_no_membership(self, legacy_user, org_alpha):
        """User with only legacy FK (no membership) cannot access — membership is source of truth."""
        assert legacy_user.can_access_organization(org_alpha) is False

    def test_legacy_fallback_rejects_other_org(self, legacy_user, org_beta):
        """Legacy user cannot access org they have no FK to."""
        assert legacy_user.can_access_organization(org_beta) is False

    def test_multi_org_access_all(self, multi_org_user, org_alpha, org_beta, org_gamma):
        """Multi-org user can access all their orgs."""
        assert multi_org_user.can_access_organization(org_alpha) is True
        assert multi_org_user.can_access_organization(org_beta) is True
        assert multi_org_user.can_access_organization(org_gamma) is True

    def test_inactive_membership_denies_access(self, owner_user, org_beta):
        """Deactivated membership denies access."""
        OrganizationMembership.no_workspace_objects.create(
            user=owner_user,
            organization=org_beta,
            role=OrganizationRoles.MEMBER,
            level=Level.MEMBER,
            is_active=False,
        )
        assert owner_user.can_access_organization(org_beta) is False

    def test_access_after_removal(self, multi_org_user, org_beta):
        """After membership is deactivated, user loses access."""
        assert multi_org_user.can_access_organization(org_beta) is True

        # Deactivate membership (simulates removal)
        membership = OrganizationMembership.no_workspace_objects.get(
            user=multi_org_user, organization=org_beta
        )
        membership.is_active = False
        membership.save()

        assert multi_org_user.can_access_organization(org_beta) is False


# ---------------------------------------------------------------------------
# Phase 1: get_membership / get_membership_level
# ---------------------------------------------------------------------------


class TestGetMembership:
    """Tests for User.get_membership() and get_membership_level()."""

    def test_get_membership_returns_active(self, owner_user, org_alpha):
        membership = owner_user.get_membership(org_alpha)
        assert membership is not None
        assert membership.role == OrganizationRoles.OWNER

    def test_get_membership_returns_none_for_no_membership(self, owner_user, org_beta):
        assert owner_user.get_membership(org_beta) is None

    def test_get_membership_returns_none_for_inactive(self, owner_user, org_beta):
        OrganizationMembership.no_workspace_objects.create(
            user=owner_user,
            organization=org_beta,
            role=OrganizationRoles.ADMIN,
            level=Level.ADMIN,
            is_active=False,
        )
        assert owner_user.get_membership(org_beta) is None

    def test_get_membership_level_from_membership(
        self, multi_org_user, org_alpha, org_beta, org_gamma
    ):
        assert multi_org_user.get_membership_level(org_alpha) == Level.OWNER
        assert multi_org_user.get_membership_level(org_beta) == Level.ADMIN
        assert multi_org_user.get_membership_level(org_gamma) == Level.VIEWER

    def test_get_membership_level_legacy_fallback(self, legacy_user, org_alpha):
        """Legacy user without membership gets level derived from FK role."""
        level = legacy_user.get_membership_level(org_alpha)
        assert level == Level.ADMIN  # legacy_user has organization_role=Admin

    def test_get_membership_level_no_access(self, owner_user, org_beta):
        assert owner_user.get_membership_level(org_beta) is None


# ---------------------------------------------------------------------------
# Phase 1: get_organization_role
# ---------------------------------------------------------------------------


class TestGetOrganizationRole:
    """Tests for User.get_organization_role()."""

    def test_role_from_membership(self, owner_user, org_alpha):
        assert owner_user.get_organization_role(org_alpha) == OrganizationRoles.OWNER

    def test_role_default_to_primary_org(self, owner_user):
        """Calling without arg uses user.organization."""
        assert owner_user.get_organization_role() == OrganizationRoles.OWNER

    def test_different_roles_per_org(
        self, multi_org_user, org_alpha, org_beta, org_gamma
    ):
        assert (
            multi_org_user.get_organization_role(org_alpha) == OrganizationRoles.OWNER
        )
        assert multi_org_user.get_organization_role(org_beta) == OrganizationRoles.ADMIN
        assert (
            multi_org_user.get_organization_role(org_gamma)
            == OrganizationRoles.MEMBER_VIEW_ONLY
        )

    def test_legacy_fallback_for_primary_org(self, legacy_user, org_alpha):
        """Legacy user falls back to user.organization_role."""
        assert legacy_user.get_organization_role(org_alpha) == OrganizationRoles.ADMIN

    def test_no_role_for_unrelated_org(self, owner_user, org_beta):
        assert owner_user.get_organization_role(org_beta) is None

    def test_no_role_when_no_org(self, db):
        """User with no organization returns None."""
        user = User.objects.create_user(
            email="orphan@test.com",
            password="testpass123",
            name="Orphan User",
        )
        assert user.get_organization_role() is None


# ---------------------------------------------------------------------------
# Phase 1: has_global_workspace_access
# ---------------------------------------------------------------------------


class TestHasGlobalWorkspaceAccess:
    """Tests for User.has_global_workspace_access()."""

    def test_owner_has_global_access(self, owner_user, org_alpha):
        assert owner_user.has_global_workspace_access(org_alpha) is True

    def test_member_no_global_access(self, member_user, org_alpha):
        """Members do NOT have global workspace access — they need explicit membership."""
        assert member_user.has_global_workspace_access(org_alpha) is False

    def test_viewer_no_global_access(self, viewer_user, org_alpha):
        """Viewers do NOT have global workspace access — they need explicit membership."""
        assert viewer_user.has_global_workspace_access(org_alpha) is False

    def test_multi_org_global_access_varies(
        self, multi_org_user, org_alpha, org_beta, org_gamma
    ):
        """Only Owner/Admin have global workspace access; Viewer does not."""
        assert multi_org_user.has_global_workspace_access(org_alpha) is True  # Owner
        assert multi_org_user.has_global_workspace_access(org_beta) is True  # Admin
        assert multi_org_user.has_global_workspace_access(org_gamma) is False  # Viewer

    def test_workspace_only_user_no_global_access(self, db, org_alpha):
        """User with workspace_member role does NOT have global access."""
        clear_workspace_context()
        set_workspace_context(organization=org_alpha)
        user = User.objects.create_user(
            email="wsonly@alpha.com",
            password="testpass123",
            name="WS Only User",
            organization=org_alpha,
            organization_role=OrganizationRoles.WORKSPACE_MEMBER,
        )
        OrganizationMembership.no_workspace_objects.create(
            user=user,
            organization=org_alpha,
            role=OrganizationRoles.WORKSPACE_MEMBER,
            is_active=True,
        )
        assert user.has_global_workspace_access(org_alpha) is False

    def test_no_access_to_unrelated_org(self, owner_user, org_beta):
        assert owner_user.has_global_workspace_access(org_beta) is False

    def test_legacy_user_global_access(self, legacy_user, org_alpha):
        """Legacy user with Admin role has global access."""
        assert legacy_user.has_global_workspace_access(org_alpha) is True


# ---------------------------------------------------------------------------
# Phase 1: is_workspace_only_user
# ---------------------------------------------------------------------------


class TestIsWorkspaceOnlyUser:
    def test_owner_is_not_workspace_only(self, owner_user, org_alpha):
        assert owner_user.is_workspace_only_user(org_alpha) is False

    def test_workspace_member_is_workspace_only(self, db, org_alpha):
        clear_workspace_context()
        set_workspace_context(organization=org_alpha)
        user = User.objects.create_user(
            email="wsmember@alpha.com",
            password="testpass123",
            name="WS Member",
            organization=org_alpha,
            organization_role=OrganizationRoles.WORKSPACE_MEMBER,
        )
        OrganizationMembership.no_workspace_objects.create(
            user=user,
            organization=org_alpha,
            role=OrganizationRoles.WORKSPACE_MEMBER,
            is_active=True,
        )
        assert user.is_workspace_only_user(org_alpha) is True


# ---------------------------------------------------------------------------
# Phase 1: can_access_workspace (cross-org)
# ---------------------------------------------------------------------------


class TestCanAccessWorkspace:
    """Tests for User.can_access_workspace() with multi-org awareness."""

    def test_owner_accesses_own_org_workspace(self, owner_user, ws_alpha_default):
        assert owner_user.can_access_workspace(ws_alpha_default) is True

    def test_owner_cannot_access_other_org_workspace(self, owner_user, ws_beta_default):
        """Owner in Alpha cannot access Beta's workspace."""
        assert owner_user.can_access_workspace(ws_beta_default) is False

    def test_multi_org_user_accesses_both_workspaces(
        self, multi_org_user, ws_alpha_default, ws_beta_default
    ):
        """Multi-org user with global access in both orgs can access both workspaces."""
        assert multi_org_user.can_access_workspace(ws_alpha_default) is True
        assert multi_org_user.can_access_workspace(ws_beta_default) is True

    def test_workspace_member_with_explicit_membership(
        self, db, org_alpha, ws_alpha_staging, owner_user
    ):
        """Workspace-only user needs explicit WorkspaceMembership."""
        clear_workspace_context()
        set_workspace_context(organization=org_alpha)
        ws_user = User.objects.create_user(
            email="wsuser@alpha.com",
            password="testpass123",
            name="WS User",
            organization=org_alpha,
            organization_role=OrganizationRoles.WORKSPACE_MEMBER,
        )
        OrganizationMembership.no_workspace_objects.create(
            user=ws_user,
            organization=org_alpha,
            role=OrganizationRoles.WORKSPACE_MEMBER,
            is_active=True,
        )

        # No workspace membership yet — cannot access
        assert ws_user.can_access_workspace(ws_alpha_staging) is False

        # Add workspace membership
        WorkspaceMembership.no_workspace_objects.create(
            workspace=ws_alpha_staging,
            user=ws_user,
            role=OrganizationRoles.WORKSPACE_MEMBER,
            is_active=True,
        )
        assert ws_user.can_access_workspace(ws_alpha_staging) is True

    def test_removed_from_org_loses_workspace_access(
        self, multi_org_user, org_beta, ws_beta_default
    ):
        """User removed from org loses workspace access in that org."""
        assert multi_org_user.can_access_workspace(ws_beta_default) is True

        # Remove from Beta
        membership = OrganizationMembership.no_workspace_objects.get(
            user=multi_org_user, organization=org_beta
        )
        membership.is_active = False
        membership.save()

        assert multi_org_user.can_access_workspace(ws_beta_default) is False


# ---------------------------------------------------------------------------
# Phase 1: get_workspace_role (cross-org)
# ---------------------------------------------------------------------------


class TestGetWorkspaceRole:
    """Tests for User.get_workspace_role() with multi-org awareness."""

    def test_owner_gets_workspace_admin_role(self, owner_user, ws_alpha_default):
        role = owner_user.get_workspace_role(ws_alpha_default)
        expected = RoleMapping.get_workspace_role(OrganizationRoles.OWNER)
        assert role == expected

    def test_viewer_gets_workspace_viewer_role(
        self, viewer_user, ws_alpha_default, org_alpha
    ):
        """Viewer with explicit workspace membership gets workspace viewer role."""
        org_mem = OrganizationMembership.no_workspace_objects.get(
            user=viewer_user, organization=org_alpha
        )
        WorkspaceMembership.no_workspace_objects.create(
            workspace=ws_alpha_default,
            user=viewer_user,
            role=OrganizationRoles.WORKSPACE_VIEWER,
            level=Level.WORKSPACE_VIEWER,
            organization_membership=org_mem,
            is_active=True,
        )
        role = viewer_user.get_workspace_role(ws_alpha_default)
        assert role == OrganizationRoles.WORKSPACE_VIEWER

    def test_multi_org_different_workspace_roles(
        self, multi_org_user, ws_alpha_default, ws_beta_default
    ):
        """Same user has different workspace roles based on org role."""
        alpha_role = multi_org_user.get_workspace_role(ws_alpha_default)
        beta_role = multi_org_user.get_workspace_role(ws_beta_default)

        # Owner in Alpha → workspace_admin
        assert alpha_role == RoleMapping.get_workspace_role(OrganizationRoles.OWNER)
        # Admin in Beta → workspace_admin
        assert beta_role == RoleMapping.get_workspace_role(OrganizationRoles.ADMIN)

    def test_no_role_for_inaccessible_workspace(self, owner_user, ws_beta_default):
        assert owner_user.get_workspace_role(ws_beta_default) is None

    def test_explicit_workspace_membership_role(
        self, db, org_alpha, ws_alpha_staging, owner_user
    ):
        """Workspace-only user gets role from WorkspaceMembership."""
        clear_workspace_context()
        set_workspace_context(organization=org_alpha)
        ws_user = User.objects.create_user(
            email="explicitrole@alpha.com",
            password="testpass123",
            name="Explicit Role User",
            organization=org_alpha,
            organization_role=OrganizationRoles.WORKSPACE_VIEWER,
        )
        OrganizationMembership.no_workspace_objects.create(
            user=ws_user,
            organization=org_alpha,
            role=OrganizationRoles.WORKSPACE_VIEWER,
            is_active=True,
        )
        WorkspaceMembership.no_workspace_objects.create(
            workspace=ws_alpha_staging,
            user=ws_user,
            role=OrganizationRoles.WORKSPACE_ADMIN,
            is_active=True,
        )

        role = ws_user.get_workspace_role(ws_alpha_staging)
        assert role == OrganizationRoles.WORKSPACE_ADMIN


# ---------------------------------------------------------------------------
# Phase 1: can_write_to_workspace / can_read_from_workspace
# ---------------------------------------------------------------------------


class TestWorkspaceWriteRead:
    """Tests for write/read permission checks with multi-org awareness."""

    def test_owner_can_write(self, owner_user, ws_alpha_default):
        assert owner_user.can_write_to_workspace(ws_alpha_default) is True

    def test_viewer_cannot_write(self, viewer_user, ws_alpha_default):
        assert viewer_user.can_write_to_workspace(ws_alpha_default) is False

    def test_viewer_can_read(self, viewer_user, ws_alpha_default, org_alpha):
        """Viewer with explicit membership can read from workspace."""
        org_mem = OrganizationMembership.no_workspace_objects.get(
            user=viewer_user, organization=org_alpha
        )
        WorkspaceMembership.no_workspace_objects.create(
            workspace=ws_alpha_default,
            user=viewer_user,
            role=OrganizationRoles.WORKSPACE_VIEWER,
            level=Level.WORKSPACE_VIEWER,
            organization_membership=org_mem,
            is_active=True,
        )
        assert viewer_user.can_read_from_workspace(ws_alpha_default) is True

    def test_member_can_write(self, member_user, ws_alpha_default, org_alpha):
        """Member with explicit membership can write to workspace."""
        org_mem = OrganizationMembership.no_workspace_objects.get(
            user=member_user, organization=org_alpha
        )
        WorkspaceMembership.no_workspace_objects.create(
            workspace=ws_alpha_default,
            user=member_user,
            role=OrganizationRoles.WORKSPACE_MEMBER,
            level=Level.WORKSPACE_MEMBER,
            organization_membership=org_mem,
            is_active=True,
        )
        assert member_user.can_write_to_workspace(ws_alpha_default) is True

    def test_member_can_read(self, member_user, ws_alpha_default, org_alpha):
        """Member with explicit membership can read from workspace."""
        org_mem = OrganizationMembership.no_workspace_objects.get(
            user=member_user, organization=org_alpha
        )
        WorkspaceMembership.no_workspace_objects.create(
            workspace=ws_alpha_default,
            user=member_user,
            role=OrganizationRoles.WORKSPACE_MEMBER,
            level=Level.WORKSPACE_MEMBER,
            organization_membership=org_mem,
            is_active=True,
        )
        assert member_user.can_read_from_workspace(ws_alpha_default) is True

    def test_no_write_to_other_org_workspace(self, owner_user, ws_beta_default):
        assert owner_user.can_write_to_workspace(ws_beta_default) is False

    def test_no_read_from_other_org_workspace(self, owner_user, ws_beta_default):
        assert owner_user.can_read_from_workspace(ws_beta_default) is False

    def test_multi_org_write_access(
        self, multi_org_user, ws_alpha_default, ws_beta_default
    ):
        """Multi-org user (Owner in Alpha, Admin in Beta) can write in both."""
        assert multi_org_user.can_write_to_workspace(ws_alpha_default) is True
        assert multi_org_user.can_write_to_workspace(ws_beta_default) is True

    def test_multi_org_viewer_needs_membership(self, multi_org_user, db, org_gamma):
        """Multi-org user as Viewer in Gamma needs explicit workspace membership."""
        clear_workspace_context()
        set_workspace_context(organization=org_gamma)
        ws_gamma = Workspace.objects.create(
            name="Gamma Default",
            organization=org_gamma,
            is_default=True,
            is_active=True,
            created_by=multi_org_user,
        )
        # Without explicit workspace membership, Viewer cannot access
        assert multi_org_user.can_write_to_workspace(ws_gamma) is False
        assert multi_org_user.can_read_from_workspace(ws_gamma) is False

        # After adding explicit workspace membership, Viewer can read but not write
        org_mem = OrganizationMembership.no_workspace_objects.get(
            user=multi_org_user, organization=org_gamma
        )
        WorkspaceMembership.no_workspace_objects.create(
            workspace=ws_gamma,
            user=multi_org_user,
            role=OrganizationRoles.WORKSPACE_VIEWER,
            organization_membership=org_mem,
            is_active=True,
        )
        assert multi_org_user.can_write_to_workspace(ws_gamma) is False
        assert multi_org_user.can_read_from_workspace(ws_gamma) is True

    def test_removed_from_org_no_write(self, multi_org_user, org_beta, ws_beta_default):
        """After removal from org, user cannot write."""
        assert multi_org_user.can_write_to_workspace(ws_beta_default) is True

        membership = OrganizationMembership.no_workspace_objects.get(
            user=multi_org_user, organization=org_beta
        )
        membership.is_active = False
        membership.save()

        assert multi_org_user.can_write_to_workspace(ws_beta_default) is False
        assert multi_org_user.can_read_from_workspace(ws_beta_default) is False


# ---------------------------------------------------------------------------
# E2E Scenarios
# ---------------------------------------------------------------------------


class TestE2EMultiOrgScenarios:
    """End-to-end scenarios that simulate real-world multi-org usage."""

    def test_scenario_user_invited_to_second_org(self, db, org_alpha, org_beta):
        """
        Scenario: Alice is Owner of Alpha. She gets invited to Beta as Member.
        She should be able to access both orgs with different roles.
        """
        clear_workspace_context()
        set_workspace_context(organization=org_alpha)

        alice = User.objects.create_user(
            email="alice@alpha.com",
            password="testpass123",
            name="Alice",
            organization=org_alpha,
            organization_role=OrganizationRoles.OWNER,
        )
        OrganizationMembership.no_workspace_objects.create(
            user=alice,
            organization=org_alpha,
            role=OrganizationRoles.OWNER,
            level=Level.OWNER,
            is_active=True,
        )

        # Alice gets invited to Beta as Member
        OrganizationMembership.no_workspace_objects.create(
            user=alice,
            organization=org_beta,
            role=OrganizationRoles.MEMBER,
            level=Level.MEMBER,
            is_active=True,
        )

        # Verify access
        assert alice.can_access_organization(org_alpha) is True
        assert alice.can_access_organization(org_beta) is True
        assert alice.get_organization_role(org_alpha) == OrganizationRoles.OWNER
        assert alice.get_organization_role(org_beta) == OrganizationRoles.MEMBER
        assert alice.get_membership_level(org_alpha) == Level.OWNER
        assert alice.get_membership_level(org_beta) == Level.MEMBER

        # Create workspaces in both orgs
        ws_a = Workspace.objects.create(
            name="Alpha WS",
            organization=org_alpha,
            is_default=True,
            is_active=True,
            created_by=alice,
        )
        clear_workspace_context()
        set_workspace_context(organization=org_beta)
        ws_b = Workspace.objects.create(
            name="Beta WS",
            organization=org_beta,
            is_default=True,
            is_active=True,
            created_by=alice,
        )

        # Alice needs explicit workspace membership in Beta (Member has no global access)
        beta_org_mem = OrganizationMembership.no_workspace_objects.get(
            user=alice, organization=org_beta
        )
        WorkspaceMembership.no_workspace_objects.create(
            workspace=ws_b,
            user=alice,
            role=OrganizationRoles.WORKSPACE_MEMBER,
            level=Level.WORKSPACE_MEMBER,
            organization_membership=beta_org_mem,
            is_active=True,
        )

        # Alice can access both workspaces
        assert alice.can_access_workspace(ws_a) is True
        assert alice.can_access_workspace(ws_b) is True
        assert alice.can_write_to_workspace(ws_a) is True  # Owner (global access)
        assert (
            alice.can_write_to_workspace(ws_b) is True
        )  # Member (explicit membership)

    def test_scenario_user_removed_from_org(self, db, org_alpha, org_beta):
        """
        Scenario: Bob belongs to both Alpha and Beta. Admin removes Bob
        from Beta. Bob should lose all access to Beta but keep Alpha.
        """
        clear_workspace_context()
        set_workspace_context(organization=org_alpha)

        bob = User.objects.create_user(
            email="bob@alpha.com",
            password="testpass123",
            name="Bob",
            organization=org_alpha,
            organization_role=OrganizationRoles.MEMBER,
        )
        OrganizationMembership.no_workspace_objects.create(
            user=bob,
            organization=org_alpha,
            role=OrganizationRoles.MEMBER,
            level=Level.MEMBER,
            is_active=True,
        )
        beta_membership = OrganizationMembership.no_workspace_objects.create(
            user=bob,
            organization=org_beta,
            role=OrganizationRoles.ADMIN,
            level=Level.ADMIN,
            is_active=True,
        )

        clear_workspace_context()
        set_workspace_context(organization=org_beta)
        ws_beta = Workspace.objects.create(
            name="Beta WS",
            organization=org_beta,
            is_default=True,
            is_active=True,
            created_by=bob,
        )

        # Before removal
        assert bob.can_access_organization(org_beta) is True
        assert bob.can_access_workspace(ws_beta) is True
        assert bob.get_organization_role(org_beta) == OrganizationRoles.ADMIN

        # Admin removes Bob from Beta (deactivate membership)
        beta_membership.is_active = False
        beta_membership.save()

        # After removal
        assert bob.can_access_organization(org_beta) is False
        assert bob.can_access_workspace(ws_beta) is False
        assert bob.get_organization_role(org_beta) is None
        assert bob.get_membership_level(org_beta) is None

        # Alpha access unchanged
        assert bob.can_access_organization(org_alpha) is True
        assert bob.get_organization_role(org_alpha) == OrganizationRoles.MEMBER

    def test_scenario_legacy_user_gets_membership(self, legacy_user, org_alpha):
        """
        Scenario: Legacy user (FK only, no membership) logs in.
        Without membership, access is denied. After backfill, access works.
        """
        # Before membership — no access (membership is source of truth)
        assert legacy_user.can_access_organization(org_alpha) is False

        # Admin backfills membership
        OrganizationMembership.no_workspace_objects.create(
            user=legacy_user,
            organization=org_alpha,
            role=OrganizationRoles.ADMIN,
            level=Level.ADMIN,
            is_active=True,
        )

        # After membership — membership path works
        assert legacy_user.can_access_organization(org_alpha) is True
        assert legacy_user.get_organization_role(org_alpha) == OrganizationRoles.ADMIN
        assert legacy_user.get_membership_level(org_alpha) == Level.ADMIN

    def test_scenario_role_upgrade_via_membership(self, member_user, org_alpha):
        """
        Scenario: Member gets promoted to Admin. The membership row is
        updated but user.organization_role is NOT (it's legacy).
        The new role should be returned from get_organization_role().
        """
        membership = OrganizationMembership.no_workspace_objects.get(
            user=member_user, organization=org_alpha
        )
        membership.role = OrganizationRoles.ADMIN
        membership.level = Level.ADMIN
        membership.save()

        # Membership takes priority over legacy field
        assert member_user.get_organization_role(org_alpha) == OrganizationRoles.ADMIN
        assert member_user.get_membership_level(org_alpha) == Level.ADMIN

        # Legacy field is still "Member" — but membership wins
        assert member_user.organization_role == OrganizationRoles.MEMBER

    def test_scenario_user_with_no_org_at_all(self, db):
        """
        Scenario: A user exists but has no organization FK and no memberships.
        All access checks should return False/None gracefully.
        """
        orphan = User.objects.create_user(
            email="orphan@nowhere.com",
            password="testpass123",
            name="Orphan",
        )
        new_org = Organization.objects.create(name="Some Org")

        assert orphan.can_access_organization(new_org) is False
        assert orphan.get_organization_role() is None
        assert orphan.get_organization_role(new_org) is None
        assert orphan.get_membership_level(new_org) is None
        assert orphan.has_global_workspace_access() is False
