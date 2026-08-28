"""
E2E tests for the member list/table endpoint and workspace management.

Covers:
- Member table status accuracy (Active, Deactivated, Pending, Expired)
- Member table filtering (status, role, search)
- Member table pagination and sorting
- Member table permission checks by role
- Workspace listing by role
- Workspace creation permissions
- Workspace switching
- Workspace member list
- Workspace membership integrity

NOTE: Response keys are camelCase because DRF CamelCaseJSONRenderer is active.
"""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from accounts.models.organization import Organization
from accounts.models.organization_invite import InviteStatus, OrganizationInvite
from accounts.models.organization_membership import OrganizationMembership
from accounts.models.user import User
from accounts.models.workspace import Workspace, WorkspaceMembership
from tfc.constants.levels import Level
from tfc.constants.roles import OrganizationRoles
from tfc.middleware.workspace_context import set_workspace_context

# ---------------------------------------------------------------------------
# URL constants
# ---------------------------------------------------------------------------
MEMBER_LIST_URL = "/accounts/organization/members/"
MEMBER_REMOVE_URL = "/accounts/organization/members/remove/"
MEMBER_ROLE_UPDATE_URL = "/accounts/organization/members/role/"
INVITE_CREATE_URL = "/accounts/organization/invite/"
INVITE_CANCEL_URL = "/accounts/organization/invite/cancel/"
WORKSPACE_LIST_URL = "/accounts/workspace/list/"
WORKSPACE_CREATE_URL = "/accounts/workspaces/"
WORKSPACE_SWITCH_URL = "/accounts/workspace/switch/"


def _ws_member_list_url(workspace_id):
    return f"/accounts/workspace/{workspace_id}/members/"


# ---------------------------------------------------------------------------
# Autouse fixture: ensure Owner has an OrganizationMembership
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _owner_membership(user, organization):
    OrganizationMembership.objects.get_or_create(
        user=user,
        organization=organization,
        defaults={
            "role": "Owner",
            "level": Level.OWNER,
            "is_active": True,
        },
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_user(organization, email, role_str, level, password="pass123"):
    set_workspace_context(organization=organization)
    u = User.objects.create_user(
        email=email,
        password=password,
        name=f"{role_str} User",
        organization=organization,
        organization_role=role_str,
    )
    OrganizationMembership.objects.create(
        user=u,
        organization=organization,
        role=role_str,
        level=level,
        is_active=True,
    )
    return u


def _make_client(user, workspace):
    from conftest import WorkspaceAwareAPIClient

    c = WorkspaceAwareAPIClient()
    c.force_authenticate(user=user)
    c.set_workspace(workspace)
    return c


def _get_results(response):
    """Extract member list results from the standard response envelope."""
    return response.data["result"]["results"]


def _get_total(response):
    return response.data["result"]["total"]


# ===================================================================
# TestMemberTableStatusAccuracy
# ===================================================================
@pytest.mark.django_db
class TestMemberTableStatusAccuracy:
    """Tests 1-7: verify the status field for different member states."""

    def test_active_member_status(self, auth_client, organization, workspace):
        """1. An active member shows status 'Active'."""
        _make_user(organization, "active@futureagi.com", "Member", Level.MEMBER)
        resp = auth_client.get(MEMBER_LIST_URL)
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        emails = {r["email"]: r for r in results}
        assert "active@futureagi.com" in emails
        assert emails["active@futureagi.com"]["status"] == "Active"

    def test_deactivated_member_status(
        self, auth_client, organization, workspace, user
    ):
        """2. A removed (deactivated) member shows status 'Deactivated'."""
        member = _make_user(organization, "deact@futureagi.com", "Member", Level.MEMBER)
        # Remove the member via the API
        resp = auth_client.delete(
            MEMBER_REMOVE_URL,
            {"user_id": str(member.id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

        # Check member list
        resp = auth_client.get(MEMBER_LIST_URL)
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        emails = {r["email"]: r for r in results}
        assert "deact@futureagi.com" in emails
        assert emails["deact@futureagi.com"]["status"] == "Deactivated"

    def test_pending_invite_status(self, auth_client, organization, workspace):
        """3. A pending invite shows status 'Pending'."""
        OrganizationInvite.objects.create(
            organization=organization,
            target_email="pending@example.com",
            level=Level.MEMBER,
        )
        resp = auth_client.get(MEMBER_LIST_URL)
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        emails = {r["email"]: r for r in results}
        assert "pending@example.com" in emails
        assert emails["pending@example.com"]["status"] == "Pending"
        assert emails["pending@example.com"]["type"] == "invite"

    def test_expired_invite_status(self, auth_client, organization, workspace):
        """4. An expired invite (>7 days old) shows status 'Expired'."""
        inv = OrganizationInvite.objects.create(
            organization=organization,
            target_email="expired@example.com",
            level=Level.MEMBER,
        )
        # Backdate the invite beyond validity period
        OrganizationInvite.objects.filter(pk=inv.pk).update(
            created_at=timezone.now() - timedelta(days=8)
        )
        resp = auth_client.get(MEMBER_LIST_URL)
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        emails = {r["email"]: r for r in results}
        assert "expired@example.com" in emails
        assert emails["expired@example.com"]["status"] == "Expired"

    def test_cancelled_invite_not_in_results(
        self, auth_client, organization, workspace
    ):
        """5. After cancelling an invite, it no longer appears in results."""
        inv = OrganizationInvite.objects.create(
            organization=organization,
            target_email="cancel@example.com",
            level=Level.MEMBER,
        )
        # Cancel the invite
        resp = auth_client.delete(
            INVITE_CANCEL_URL,
            {"invite_id": str(inv.id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

        resp = auth_client.get(MEMBER_LIST_URL)
        results = _get_results(resp)
        emails = [r["email"] for r in results]
        assert "cancel@example.com" not in emails

    def test_reinvite_deactivated_member_becomes_active(
        self, auth_client, organization, workspace, user
    ):
        """6. Re-inviting a deactivated member restores them to Active."""
        member = _make_user(
            organization, "reinvite@futureagi.com", "Member", Level.MEMBER
        )
        # Remove
        auth_client.delete(
            MEMBER_REMOVE_URL,
            {"user_id": str(member.id)},
            format="json",
        )
        # Re-invite (the user is an existing active user, so the invite
        # is auto-deleted and the membership is restored)
        resp = auth_client.post(
            INVITE_CREATE_URL,
            {"emails": ["reinvite@futureagi.com"], "org_level": Level.MEMBER},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

        resp = auth_client.get(MEMBER_LIST_URL)
        results = _get_results(resp)
        emails = {r["email"]: r for r in results}
        assert "reinvite@futureagi.com" in emails
        assert emails["reinvite@futureagi.com"]["status"] == "Active"

    def test_role_update_reflected_in_list(self, auth_client, organization, workspace):
        """7. After updating a member's role, the list shows the new role."""
        member = _make_user(
            organization, "roleup@futureagi.com", "Member", Level.MEMBER
        )
        # Update role from Member to Admin
        resp = auth_client.post(
            MEMBER_ROLE_UPDATE_URL,
            {"user_id": str(member.id), "org_level": Level.ADMIN},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

        resp = auth_client.get(MEMBER_LIST_URL)
        results = _get_results(resp)
        emails = {r["email"]: r for r in results}
        assert emails["roleup@futureagi.com"]["org_role"] == "Admin"
        assert emails["roleup@futureagi.com"]["org_level"] == Level.ADMIN


# ===================================================================
# TestMemberTableFiltering
# ===================================================================
@pytest.mark.django_db
class TestMemberTableFiltering:
    """Tests 8-18: filtering by status, role, and search."""

    @pytest.fixture(autouse=True)
    def _setup_members(self, organization, workspace, user):
        """Create a mix of members and invites for filtering tests."""
        self.admin = _make_user(
            organization, "admin@futureagi.com", "Admin", Level.ADMIN
        )
        self.member = _make_user(
            organization, "member@futureagi.com", "Member", Level.MEMBER
        )
        self.viewer = _make_user(
            organization, "viewer@futureagi.com", "Viewer", Level.VIEWER
        )

        # Pending invite
        self.pending_invite = OrganizationInvite.objects.create(
            organization=organization,
            target_email="pend-filter@example.com",
            level=Level.MEMBER,
        )

        # Expired invite
        self.expired_invite = OrganizationInvite.objects.create(
            organization=organization,
            target_email="exp-filter@example.com",
            level=Level.VIEWER,
        )
        OrganizationInvite.objects.filter(pk=self.expired_invite.pk).update(
            created_at=timezone.now() - timedelta(days=8)
        )

    def test_filter_status_active(self, auth_client):
        """8. filter_status=Active returns only active members."""
        resp = auth_client.get(MEMBER_LIST_URL, {"filter_status": "Active"})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        assert all(r["status"] == "Active" for r in results)
        assert len(results) >= 4  # owner + admin + member + viewer

    def test_filter_status_pending(self, auth_client):
        """9. filter_status=Pending returns only pending invites."""
        resp = auth_client.get(MEMBER_LIST_URL, {"filter_status": "Pending"})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        assert all(r["status"] == "Pending" for r in results)
        assert len(results) >= 1

    def test_filter_status_expired(self, auth_client):
        """10. filter_status=Expired returns only expired invites."""
        resp = auth_client.get(MEMBER_LIST_URL, {"filter_status": "Expired"})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        assert all(r["status"] == "Expired" for r in results)
        assert len(results) >= 1

    def test_filter_status_active_and_pending(self, auth_client):
        """11. filter_status=Active,Pending returns both."""
        resp = auth_client.get(
            MEMBER_LIST_URL, {"filter_status": ["Active", "Pending"]}
        )
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        statuses = {r["status"] for r in results}
        assert statuses <= {"Active", "Pending"}
        assert "Active" in statuses
        assert "Pending" in statuses

    def test_filter_role_owner(self, auth_client):
        """12. filter_role=org_15 returns only Owners."""
        resp = auth_client.get(MEMBER_LIST_URL, {"filter_role": "org_15"})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        assert len(results) >= 1
        assert all(r["org_level"] == Level.OWNER for r in results)

    def test_filter_role_admin(self, auth_client):
        """13. filter_role=org_8 returns only Admins."""
        resp = auth_client.get(MEMBER_LIST_URL, {"filter_role": "org_8"})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        assert len(results) >= 1
        assert all(r["org_level"] == Level.ADMIN for r in results)

    def test_filter_role_member(self, auth_client):
        """14. filter_role=org_3 returns only Members."""
        resp = auth_client.get(MEMBER_LIST_URL, {"filter_role": "org_3"})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        assert len(results) >= 1
        assert all(r["org_level"] == Level.MEMBER for r in results)

    def test_filter_role_viewer(self, auth_client):
        """15. filter_role=org_1 returns only Viewers."""
        resp = auth_client.get(MEMBER_LIST_URL, {"filter_role": "org_1"})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        assert len(results) >= 1
        assert all(r["org_level"] == Level.VIEWER for r in results)

    def test_search_by_name(self, auth_client):
        """16. search by name substring matches."""
        resp = auth_client.get(MEMBER_LIST_URL, {"search": "Admin User"})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        assert any(r["email"] == "admin@futureagi.com" for r in results)

    def test_search_by_email(self, auth_client):
        """17. search by email substring matches."""
        resp = auth_client.get(MEMBER_LIST_URL, {"search": "viewer@"})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        assert any(r["email"] == "viewer@futureagi.com" for r in results)

    def test_combined_search_and_filter_status(self, auth_client):
        """18. Combined search + filter_status returns intersection."""
        resp = auth_client.get(
            MEMBER_LIST_URL,
            {"search": "member", "filter_status": "Active"},
        )
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        assert all(r["status"] == "Active" for r in results)
        # Should include the member user but not the pending/expired invites
        emails = [r["email"] for r in results]
        assert "member@futureagi.com" in emails


# ===================================================================
# TestMemberTablePagination
# ===================================================================
@pytest.mark.django_db
class TestMemberTablePagination:
    """Tests 19-25: pagination and sorting."""

    @pytest.fixture(autouse=True)
    def _setup_many_members(self, organization, workspace, user):
        """Create 10+ members for pagination tests."""
        for i in range(12):
            _make_user(
                organization,
                f"page{i:02d}@futureagi.com",
                "Member",
                Level.MEMBER,
            )

    def test_page_1_limit_5(self, auth_client):
        """19. page=1, limit=5 returns 5 results with total >= 13."""
        resp = auth_client.get(MEMBER_LIST_URL, {"page": 1, "limit": 5})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        assert len(results) == 5
        assert _get_total(resp) >= 13  # 1 owner + 12 members

    def test_page_2_limit_5(self, auth_client):
        """20. page=2, limit=5 returns next batch."""
        resp = auth_client.get(MEMBER_LIST_URL, {"page": 2, "limit": 5})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        assert len(results) == 5

    def test_page_beyond_data(self, auth_client):
        """21. Requesting page far beyond data returns empty results."""
        resp = auth_client.get(MEMBER_LIST_URL, {"page": 100, "limit": 5})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        assert len(results) == 0

    def test_sort_by_name_asc(self, auth_client):
        """22. sort=name sorts alphabetically."""
        resp = auth_client.get(MEMBER_LIST_URL, {"sort": "name", "limit": 50})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        names = [r["name"] for r in results]
        assert names == sorted(names)

    def test_sort_by_name_desc(self, auth_client):
        """23. sort=-name sorts reverse alphabetically."""
        resp = auth_client.get(MEMBER_LIST_URL, {"sort": "-name", "limit": 50})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        names = [r["name"] for r in results]
        assert names == sorted(names, reverse=True)

    def test_sort_by_org_level(self, auth_client):
        """24. sort=org_level sorts by level ascending."""
        resp = auth_client.get(MEMBER_LIST_URL, {"sort": "org_level", "limit": 50})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        levels = [r["org_level"] for r in results]
        assert levels == sorted(levels)

    def test_sort_by_created_at_desc(self, auth_client):
        """25. sort=-created_at sorts newest first (default)."""
        resp = auth_client.get(MEMBER_LIST_URL, {"sort": "-created_at", "limit": 50})
        assert resp.status_code == status.HTTP_200_OK
        results = _get_results(resp)
        dates = [r["created_at"] for r in results]
        assert dates == sorted(dates, reverse=True)


# ===================================================================
# TestMemberTablePermissions
# ===================================================================
@pytest.mark.django_db
class TestMemberTablePermissions:
    """Tests 26-30: role-based access to the member list endpoint."""

    def test_owner_can_view(self, auth_client):
        """26. Owner can view the member list."""
        resp = auth_client.get(MEMBER_LIST_URL)
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_can_view(self, organization, workspace):
        """27. Admin can view the member list."""
        admin = _make_user(
            organization, "admin-perm@futureagi.com", "Admin", Level.ADMIN
        )
        client = _make_client(admin, workspace)
        resp = client.get(MEMBER_LIST_URL)
        assert resp.status_code == status.HTTP_200_OK
        client.stop_workspace_injection()

    def test_member_cannot_view(self, organization, workspace):
        """28. Member gets 403 (IsOrganizationAdmin required)."""
        member = _make_user(
            organization, "member-perm@futureagi.com", "Member", Level.MEMBER
        )
        client = _make_client(member, workspace)
        resp = client.get(MEMBER_LIST_URL)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        client.stop_workspace_injection()

    def test_viewer_cannot_view(self, organization, workspace):
        """29. Viewer gets 403."""
        viewer = _make_user(
            organization, "viewer-perm@futureagi.com", "Viewer", Level.VIEWER
        )
        client = _make_client(viewer, workspace)
        resp = client.get(MEMBER_LIST_URL)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        client.stop_workspace_injection()

    def test_unauthenticated_cannot_view(self, api_client):
        """30. Unauthenticated user gets 401 or 403."""
        resp = api_client.get(MEMBER_LIST_URL)
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


# ===================================================================
# TestWorkspaceListByRole
# ===================================================================
@pytest.mark.django_db
class TestWorkspaceListByRole:
    """Tests 31-35: workspace visibility differs by org role."""

    @pytest.fixture(autouse=True)
    def _setup_workspaces(self, organization, workspace, user):
        """Create a second workspace. Give explicit WS membership only for default."""
        self.default_ws = workspace
        self.staging_ws = Workspace.objects.create(
            name="Staging",
            organization=organization,
            is_default=False,
            is_active=True,
            created_by=user,
        )

    def test_owner_sees_all_workspaces(self, auth_client):
        """31. Owner lists all workspaces."""
        resp = auth_client.get(WORKSPACE_LIST_URL)
        assert resp.status_code == status.HTTP_200_OK
        ws_names = [w["name"] for w in resp.data["results"]]
        assert "Test Workspace" in ws_names
        assert "Staging" in ws_names

    def test_admin_sees_all_workspaces(self, organization, workspace):
        """32. Admin lists all workspaces."""
        admin = _make_user(organization, "admin-ws@futureagi.com", "Admin", Level.ADMIN)
        client = _make_client(admin, workspace)
        resp = client.get(WORKSPACE_LIST_URL)
        assert resp.status_code == status.HTTP_200_OK
        ws_names = [w["name"] for w in resp.data["results"]]
        assert "Test Workspace" in ws_names
        assert "Staging" in ws_names
        client.stop_workspace_injection()

    def test_member_sees_only_assigned_workspaces(self, organization, workspace, user):
        """33. Org Member only sees workspaces with explicit membership."""
        member = _make_user(
            organization, "member-ws@futureagi.com", "Member", Level.MEMBER
        )
        # Give explicit WS membership to default WS only
        org_mem = OrganizationMembership.objects.get(
            user=member, organization=organization
        )
        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=member,
            role="workspace_member",
            level=Level.WORKSPACE_MEMBER,
            organization_membership=org_mem,
            is_active=True,
        )
        client = _make_client(member, workspace)
        resp = client.get(WORKSPACE_LIST_URL)
        assert resp.status_code == status.HTTP_200_OK
        ws_names = [w["name"] for w in resp.data["results"]]
        # Members only see workspaces they have explicit membership for
        assert "Test Workspace" in ws_names
        assert "Staging" not in ws_names
        client.stop_workspace_injection()

    def test_viewer_sees_only_assigned_workspaces(self, organization, workspace, user):
        """34. Org Viewer only sees workspaces with explicit membership."""
        viewer = _make_user(
            organization, "viewer-ws@futureagi.com", "Viewer", Level.VIEWER
        )
        org_mem = OrganizationMembership.objects.get(
            user=viewer, organization=organization
        )
        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=viewer,
            role="workspace_viewer",
            level=Level.WORKSPACE_VIEWER,
            organization_membership=org_mem,
            is_active=True,
        )
        client = _make_client(viewer, workspace)
        resp = client.get(WORKSPACE_LIST_URL)
        assert resp.status_code == status.HTTP_200_OK
        ws_names = [w["name"] for w in resp.data["results"]]
        # Viewers only see workspaces they have explicit membership for
        assert "Test Workspace" in ws_names
        assert "Staging" not in ws_names
        client.stop_workspace_injection()

    def test_owner_can_create_workspace(self, auth_client, organization):
        """35. Owner can create a workspace."""
        resp = auth_client.post(
            WORKSPACE_CREATE_URL,
            {
                "name": "NewWorkspace",
                "emails": [],
                "role": "workspace_admin",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert Workspace.objects.filter(
            name="NewWorkspace", organization=organization
        ).exists()


# ===================================================================
# TestWorkspaceCreatePermissions
# ===================================================================
@pytest.mark.django_db
class TestWorkspaceCreatePermissions:
    """Tests 36-38: only Owner/Admin can create workspaces."""

    def test_owner_creates_workspace(self, auth_client, organization):
        """36. Owner creates workspace -> ALLOW."""
        resp = auth_client.post(
            WORKSPACE_CREATE_URL,
            {"name": "OwnerWS", "emails": [], "role": "workspace_admin"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED

    def test_admin_creates_workspace(self, organization, workspace):
        """37. Admin creates workspace -> ALLOW."""
        admin = _make_user(organization, "admin-cr@futureagi.com", "Admin", Level.ADMIN)
        client = _make_client(admin, workspace)
        resp = client.post(
            WORKSPACE_CREATE_URL,
            {"name": "AdminWS", "emails": [], "role": "workspace_admin"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        client.stop_workspace_injection()

    def test_member_cannot_create_workspace(self, organization, workspace):
        """38. Member creates workspace -> DENY (403)."""
        member = _make_user(
            organization, "member-cr@futureagi.com", "Member", Level.MEMBER
        )
        client = _make_client(member, workspace)
        resp = client.post(
            WORKSPACE_CREATE_URL,
            {"name": "MemberWS", "emails": [], "role": "workspace_admin"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        client.stop_workspace_injection()


# ===================================================================
# TestWorkspaceSwitching
# ===================================================================
@pytest.mark.django_db
class TestWorkspaceSwitching:
    """Tests 39-40: workspace switch within and across orgs."""

    def test_switch_within_same_org(self, auth_client, organization, workspace, user):
        """39. Switch to another workspace in the same org -> success."""
        ws2 = Workspace.objects.create(
            name="SwitchTarget",
            organization=organization,
            is_default=False,
            is_active=True,
            created_by=user,
        )
        resp = auth_client.post(
            WORKSPACE_SWITCH_URL,
            {"new_workspace_id": str(ws2.id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_switch_to_different_org_denied(self, auth_client, user):
        """40. Switch to a workspace in a different org -> DENY."""
        other_org = Organization.objects.create(name="Other Org")
        other_ws = Workspace.objects.create(
            name="OtherWS",
            organization=other_org,
            is_default=True,
            is_active=True,
            created_by=user,
        )
        resp = auth_client.post(
            WORKSPACE_SWITCH_URL,
            {"new_workspace_id": str(other_ws.id)},
            format="json",
        )
        # Should get 404 or 400 — workspace doesn't belong to user's org
        assert resp.status_code in (
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST,
        )


# ===================================================================
# TestWorkspaceMemberList
# ===================================================================
@pytest.mark.django_db
class TestWorkspaceMemberList:
    """Tests 41-45: workspace-scoped member list endpoint."""

    @pytest.fixture(autouse=True)
    def _setup(self, organization, workspace, user):
        """Create WS membership for the owner + an explicit member."""
        owner_org_mem = OrganizationMembership.objects.get(
            user=user, organization=organization
        )
        # Owner may not have explicit WS membership — create one
        WorkspaceMembership.objects.get_or_create(
            workspace=workspace,
            user=user,
            defaults={
                "role": "workspace_admin",
                "level": Level.WORKSPACE_ADMIN,
                "organization_membership": owner_org_mem,
                "is_active": True,
            },
        )
        # Create an Admin who auto-accesses (no explicit WS membership)
        self.admin = _make_user(
            organization, "wsadmin@futureagi.com", "Admin", Level.ADMIN
        )
        # Create a Member with explicit WS membership
        self.ws_member = _make_user(
            organization, "wsmem@futureagi.com", "Member", Level.MEMBER
        )
        ws_mem_org = OrganizationMembership.objects.get(
            user=self.ws_member, organization=organization
        )
        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=self.ws_member,
            role="workspace_member",
            level=Level.WORKSPACE_MEMBER,
            organization_membership=ws_mem_org,
            is_active=True,
        )

    def test_ws_member_list_includes_auto_access(self, auth_client, workspace):
        """41. WS member list includes org Admin+ with auto-access."""
        resp = auth_client.get(_ws_member_list_url(workspace.id))
        assert resp.status_code == status.HTTP_200_OK
        results = resp.data["result"]["results"]
        emails = [r["email"] for r in results]
        assert "wsadmin@futureagi.com" in emails

    def test_auto_access_shows_ws_admin_role(self, auth_client, workspace):
        """42. Org Admin+ auto-access user shown with WS Admin role."""
        resp = auth_client.get(_ws_member_list_url(workspace.id))
        results = resp.data["result"]["results"]
        admin_row = next(r for r in results if r["email"] == "wsadmin@futureagi.com")
        assert admin_row["ws_role"] == "Workspace Admin"
        assert admin_row["ws_level"] == Level.WORKSPACE_ADMIN

    def test_explicit_ws_member_shows_their_role(self, auth_client, workspace):
        """43. Explicit WS member shown with their assigned WS role."""
        resp = auth_client.get(_ws_member_list_url(workspace.id))
        results = resp.data["result"]["results"]
        mem_row = next(r for r in results if r["email"] == "wsmem@futureagi.com")
        assert mem_row["ws_role"] == "Workspace Member"
        assert mem_row["ws_level"] == Level.WORKSPACE_MEMBER

    def test_ws_member_list_denied_for_non_admin(self, organization, workspace):
        """44. WS member list as non-admin -> DENY."""
        viewer = _make_user(
            organization, "wsviewer@futureagi.com", "Viewer", Level.VIEWER
        )
        client = _make_client(viewer, workspace)
        resp = client.get(_ws_member_list_url(workspace.id))
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        client.stop_workspace_injection()

    def test_default_workspace_has_creator_as_member(
        self, auth_client, workspace, user
    ):
        """45. Default workspace has the creator as a member."""
        resp = auth_client.get(_ws_member_list_url(workspace.id))
        results = resp.data["result"]["results"]
        emails = [r["email"] for r in results]
        assert user.email in emails


# ===================================================================
# TestWorkspaceMembershipIntegrity
# ===================================================================
@pytest.mark.django_db
class TestWorkspaceMembershipIntegrity:
    """Tests 46-50: data integrity constraints on workspace membership."""

    def test_ws_membership_linked_to_org_membership(
        self, organization, workspace, user
    ):
        """46. WS membership can be linked to an org membership FK."""
        member = _make_user(organization, "link@futureagi.com", "Member", Level.MEMBER)
        org_mem = OrganizationMembership.objects.get(
            user=member, organization=organization
        )
        ws_mem = WorkspaceMembership.objects.create(
            workspace=workspace,
            user=member,
            role="workspace_member",
            level=Level.WORKSPACE_MEMBER,
            organization_membership=org_mem,
            is_active=True,
        )
        assert ws_mem.organization_membership == org_mem
        assert ws_mem.organization_membership.organization == organization

    def test_workspace_name_unique_per_org(self, organization, user):
        """47. Workspace name is unique per organization."""
        from django.db import IntegrityError

        Workspace.objects.create(
            name="UniqueTest",
            organization=organization,
            is_active=True,
            created_by=user,
        )
        with pytest.raises(IntegrityError):
            Workspace.objects.create(
                name="UniqueTest",
                organization=organization,
                is_active=True,
                created_by=user,
            )

    def test_default_workspace_created_with_org(self, workspace, organization):
        """48. Default workspace exists and is_default=True."""
        default_ws = Workspace.objects.filter(
            organization=organization, is_default=True
        )
        assert default_ws.exists()
        assert default_ws.first().pk == workspace.pk

    def test_deactivated_ws_member_not_in_active_list(
        self, auth_client, organization, workspace, user
    ):
        """49. Deactivated WS member is not in active WS member list."""
        member = _make_user(
            organization, "deactws@futureagi.com", "Member", Level.MEMBER
        )
        org_mem = OrganizationMembership.objects.get(
            user=member, organization=organization
        )
        ws_mem = WorkspaceMembership.objects.create(
            workspace=workspace,
            user=member,
            role="workspace_member",
            level=Level.WORKSPACE_MEMBER,
            organization_membership=org_mem,
            is_active=True,
        )
        # Deactivate
        ws_mem.is_active = False
        ws_mem.save()

        resp = auth_client.get(_ws_member_list_url(workspace.id))
        results = resp.data["result"]["results"]
        emails = [r["email"] for r in results]
        assert "deactws@futureagi.com" not in emails

    def test_ws_only_user_cannot_see_other_workspaces(
        self, organization, workspace, user
    ):
        """50. A workspace-only user (no org role, no org membership) sees only
        workspaces where they have explicit membership.

        All standard org roles (Owner/Admin/Member/Viewer) grant global
        workspace access in this system.  So we create a user with
        organization_role=None and NO OrganizationMembership row, giving
        them only a direct WorkspaceMembership to the default workspace.
        """
        ws_user = User.objects.create_user(
            email="wsonly@futureagi.com",
            password="pass123",
            name="WS Only",
            organization=organization,
            organization_role=None,
        )
        # No OrganizationMembership — this user is workspace-only
        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=ws_user,
            role="workspace_viewer",
            level=Level.WORKSPACE_VIEWER,
            is_active=True,
        )
        # Create another workspace they do NOT have membership to
        ws2 = Workspace.objects.create(
            name="Secret WS",
            organization=organization,
            is_default=False,
            is_active=True,
            created_by=user,
        )
        client = _make_client(ws_user, workspace)
        resp = client.get(WORKSPACE_LIST_URL)
        assert resp.status_code == status.HTTP_200_OK
        ws_names = [w["name"] for w in resp.data["results"]]
        # With no org role and no org membership, has_global_workspace_access is False
        # so user should only see workspaces where they have explicit membership
        assert "Test Workspace" in ws_names
        assert "Secret WS" not in ws_names
        client.stop_workspace_injection()
