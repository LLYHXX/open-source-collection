from unittest.mock import patch

import pytest

from agentcc.models.org_config import AgentccOrgConfig
from agentcc.services.config_push import _build_payload


@pytest.mark.integration
@pytest.mark.api
class TestGatewayBudgetActionModes:
    @patch("agentcc.services.config_push._assemble_providers", return_value={})
    def test_build_payload_maps_budget_actions_to_gateway_hard_flags(
        self, _mock_providers
    ):
        config = AgentccOrgConfig(
            budgets={
                "enabled": True,
                "org_limit": 100,
                "action": "block",
                "teams": {
                    "engineering": {"limit": 50, "action": "warn"},
                    "sales": {"limit": 75, "action": "block"},
                    "ops": {"limit": 25, "action": "throttle"},
                },
            }
        )

        payload = _build_payload("org-123", config)

        budgets = payload["budgets"]
        assert budgets["action"] == "block"
        assert budgets["hard_limit"] is True
        assert budgets["teams"]["engineering"]["action"] == "warn"
        assert budgets["teams"]["engineering"]["hard"] is False
        assert budgets["teams"]["sales"]["action"] == "block"
        assert budgets["teams"]["sales"]["hard"] is True
        assert budgets["teams"]["ops"]["action"] == "throttle"
        assert budgets["teams"]["ops"]["hard"] is False

    @patch("agentcc.services.config_push._assemble_providers", return_value={})
    def test_build_payload_flattens_organization_budget_for_gateway(
        self, _mock_providers
    ):
        config = AgentccOrgConfig(
            budgets={
                "enabled": True,
                "organization": {
                    "limit": 125,
                    "period": "monthly",
                    "action": "block",
                },
            }
        )

        payload = _build_payload("org-123", config)

        budgets = payload["budgets"]
        assert budgets["org_limit"] == 125
        assert budgets["org_period"] == "monthly"
        assert budgets["action"] == "block"
        assert budgets["hard_limit"] is True

    @patch("agentcc.services.config_push._assemble_providers", return_value={})
    def test_build_payload_supports_action_mode_alias_for_nested_levels(
        self, _mock_providers
    ):
        config = AgentccOrgConfig(
            budgets={
                "enabled": True,
                "users": {
                    "alice": {"limit": 20, "action_mode": "block"},
                },
                "keys": {
                    "svc-key": {"limit": 10, "action_mode": "warn"},
                },
                "tags": {
                    "env:prod": {"limit": 5, "action_mode": "throttle"},
                },
            }
        )

        payload = _build_payload("org-123", config)

        budgets = payload["budgets"]
        assert budgets["users"]["alice"]["action"] == "block"
        assert budgets["users"]["alice"]["hard"] is True
        assert budgets["keys"]["svc-key"]["action"] == "warn"
        assert budgets["keys"]["svc-key"]["hard"] is False
        assert budgets["tags"]["env:prod"]["action"] == "throttle"
        assert budgets["tags"]["env:prod"]["hard"] is False

    @patch("agentcc.services.config_push._assemble_providers", return_value={})
    def test_build_payload_supports_org_alias_with_action_mode(self, _mock_providers):
        config = AgentccOrgConfig(
            budgets={
                "enabled": True,
                "org": {
                    "limit": 80,
                    "period": "monthly",
                    "action_mode": "warn",
                },
            }
        )

        payload = _build_payload("org-123", config)

        budgets = payload["budgets"]
        assert budgets["org_limit"] == 80
        assert budgets["org_period"] == "monthly"
        assert budgets["action"] == "warn"
        assert budgets["hard_limit"] is False

    @patch("agentcc.services.config_push._assemble_providers", return_value={})
    def test_build_payload_normalizes_flat_org_limit_object_shape(
        self, _mock_providers
    ):
        config = AgentccOrgConfig(
            budgets={
                "enabled": True,
                "org_limit": {
                    "limit": 125,
                    "period": "monthly",
                    "on_exceed": "block",
                },
            }
        )

        payload = _build_payload("org-123", config)

        budgets = payload["budgets"]
        assert budgets["org_limit"] == 125
        assert budgets["org_period"] == "monthly"
        assert budgets["action"] == "block"
        assert budgets["hard_limit"] is True
