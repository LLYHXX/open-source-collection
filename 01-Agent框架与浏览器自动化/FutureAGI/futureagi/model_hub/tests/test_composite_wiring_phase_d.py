"""
Tests for Phase 7 wiring — Phase D (picker → backend plumbing).

Covers:
- `UserEvalSerializer` accepts and validates `composite_weight_overrides`
- `CompositeChildItem.required_keys` is populated on the detail API
"""

import pytest

from model_hub.models.choices import OwnerChoices
from model_hub.models.evals_metric import CompositeEvalChild, EvalTemplate
from model_hub.serializers.eval_runner import UserEvalSerializer


@pytest.mark.django_db
class TestUserEvalSerializerCompositeWeightOverrides:
    def _payload(self, **overrides):
        base = {
            "name": "phase-d-metric",
            "template_id": "550e8400-e29b-41d4-a716-446655440000",
            "config": {"mapping": {}},
        }
        base.update(overrides)
        return base

    def test_accepts_valid_overrides(self):
        ser = UserEvalSerializer(
            data=self._payload(
                composite_weight_overrides={"child-a": 0.25, "child-b": 1.5}
            )
        )
        assert ser.is_valid(), ser.errors
        assert ser.validated_data["composite_weight_overrides"] == {
            "child-a": 0.25,
            "child-b": 1.5,
        }

    def test_coerces_integer_weights_to_float(self):
        ser = UserEvalSerializer(
            data=self._payload(composite_weight_overrides={"child-a": 2})
        )
        assert ser.is_valid(), ser.errors
        assert ser.validated_data["composite_weight_overrides"] == {"child-a": 2.0}

    def test_rejects_non_dict_overrides(self):
        ser = UserEvalSerializer(
            data=self._payload(composite_weight_overrides=["child-a", 1.0])
        )
        assert not ser.is_valid()
        assert "composite_weight_overrides" in ser.errors

    def test_rejects_non_numeric_weight(self):
        ser = UserEvalSerializer(
            data=self._payload(composite_weight_overrides={"child-a": "heavy"})
        )
        assert not ser.is_valid()
        assert "composite_weight_overrides" in ser.errors

    def test_missing_field_is_optional(self):
        ser = UserEvalSerializer(data=self._payload())
        assert ser.is_valid(), ser.errors
        assert ser.validated_data.get("composite_weight_overrides") is None

    def test_empty_dict_normalises_to_none(self):
        ser = UserEvalSerializer(data=self._payload(composite_weight_overrides={}))
        assert ser.is_valid(), ser.errors
        assert ser.validated_data["composite_weight_overrides"] is None


@pytest.mark.django_db
class TestCompositeDetailIncludesRequiredKeys:
    def test_required_keys_surface_from_child_config(
        self, auth_client, organization, workspace
    ):
        child_with_keys = EvalTemplate.no_workspace_objects.create(
            name="child-with-keys",
            organization=organization,
            workspace=workspace,
            owner=OwnerChoices.USER.value,
            config={
                "output": "Pass/Fail",
                "required_keys": ["input", "expected_output"],
            },
            eval_tags=["llm"],
        )
        child_no_keys = EvalTemplate.no_workspace_objects.create(
            name="child-no-keys",
            organization=organization,
            workspace=workspace,
            owner=OwnerChoices.USER.value,
            config={"output": "score"},
            eval_tags=["code", "function"],
        )

        create_resp = auth_client.post(
            "/model-hub/eval-templates/create-composite/",
            {
                "name": "phase-d-composite",
                "child_template_ids": [str(child_with_keys.id), str(child_no_keys.id)],
            },
            format="json",
        )
        assert create_resp.status_code == 200, create_resp.data
        composite_id = create_resp.data["result"]["id"]

        detail_resp = auth_client.get(
            f"/model-hub/eval-templates/{composite_id}/composite/"
        )
        assert detail_resp.status_code == 200, detail_resp.data
        children = detail_resp.data["result"]["children"]
        assert len(children) == 2

        by_name = {c["child_name"]: c for c in children}
        assert by_name["child-with-keys"]["required_keys"] == [
            "input",
            "expected_output",
        ]
        assert by_name["child-no-keys"]["required_keys"] == []
