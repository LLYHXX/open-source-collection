"""
Tests for Phase 7 wiring — Phase A (schema).

Covers the model/migration additions from the composite wiring plan:
- Evaluation.parent_evaluation (self-FK)
- UserEvalMetric.composite_weight_overrides (JSONField)
"""

import uuid

import pytest

from model_hub.models.choices import DatasetSourceChoices, OwnerChoices
from model_hub.models.develop_dataset import Dataset
from model_hub.models.evals_metric import EvalTemplate, UserEvalMetric
from model_hub.models.evaluation import Evaluation, StatusChoices


@pytest.fixture
def single_template(db, organization, workspace):
    return EvalTemplate.no_workspace_objects.create(
        name="wiring-single",
        organization=organization,
        workspace=workspace,
        owner=OwnerChoices.USER.value,
        config={"output": "Pass/Fail"},
    )


@pytest.fixture
def composite_template(db, organization, workspace):
    return EvalTemplate.no_workspace_objects.create(
        name="wiring-composite",
        organization=organization,
        workspace=workspace,
        owner=OwnerChoices.USER.value,
        template_type="composite",
        config={},
    )


@pytest.fixture
def dataset(db, organization, workspace):
    return Dataset.objects.create(
        name="wiring-dataset",
        organization=organization,
        workspace=workspace,
        source=DatasetSourceChoices.BUILD.value,
    )


def _make_evaluation(user, organization, workspace, template, **overrides):
    return Evaluation.objects.create(
        user=user,
        organization=organization,
        workspace=workspace,
        eval_template=template,
        status=StatusChoices.PENDING,
        **overrides,
    )


@pytest.mark.django_db
class TestEvaluationParentFK:
    def test_parent_evaluation_defaults_to_none(
        self, user, organization, workspace, single_template
    ):
        ev = _make_evaluation(user, organization, workspace, single_template)
        assert ev.parent_evaluation is None
        assert ev.child_evaluations.count() == 0

    def test_child_links_to_parent(
        self, user, organization, workspace, composite_template, single_template
    ):
        parent = _make_evaluation(user, organization, workspace, composite_template)
        child_a = _make_evaluation(
            user,
            organization,
            workspace,
            single_template,
            parent_evaluation=parent,
        )
        child_b = _make_evaluation(
            user,
            organization,
            workspace,
            single_template,
            parent_evaluation=parent,
        )
        assert parent.child_evaluations.count() == 2
        assert {c.id for c in parent.child_evaluations.all()} == {
            child_a.id,
            child_b.id,
        }

    def test_soft_delete_child_drops_from_parent_relation(
        self, user, organization, workspace, composite_template, single_template
    ):
        """Evaluation uses BaseModel soft-delete; the default manager filters
        out deleted=True rows. A soft-deleted child should disappear from
        `parent.child_evaluations`, but the FK value stays on the underlying
        row so analytics can still join through `all_objects` / raw queries.
        """
        parent = _make_evaluation(user, organization, workspace, composite_template)
        child = _make_evaluation(
            user,
            organization,
            workspace,
            single_template,
            parent_evaluation=parent,
        )
        assert parent.child_evaluations.count() == 1

        child.delete()  # soft delete
        assert parent.child_evaluations.count() == 0

    def test_children_query_by_parent(
        self, user, organization, workspace, composite_template, single_template
    ):
        parent = _make_evaluation(user, organization, workspace, composite_template)
        _make_evaluation(
            user,
            organization,
            workspace,
            single_template,
            parent_evaluation=parent,
        )
        standalone = _make_evaluation(user, organization, workspace, single_template)

        children = Evaluation.objects.filter(parent_evaluation=parent)
        assert children.count() == 1
        assert standalone.id not in children.values_list("id", flat=True)


@pytest.mark.django_db
class TestUserEvalMetricCompositeWeightOverrides:
    def _make_metric(self, organization, workspace, template, dataset, **overrides):
        return UserEvalMetric.objects.create(
            name=f"wiring-metric-{uuid.uuid4().hex[:6]}",
            organization=organization,
            workspace=workspace,
            template=template,
            dataset=dataset,
            config={},
            **overrides,
        )

    def test_default_is_none(
        self, organization, workspace, composite_template, dataset
    ):
        metric = self._make_metric(organization, workspace, composite_template, dataset)
        assert metric.composite_weight_overrides is None

    def test_persists_override_map(
        self, organization, workspace, composite_template, dataset
    ):
        child_id_a = str(uuid.uuid4())
        child_id_b = str(uuid.uuid4())
        overrides = {child_id_a: 0.25, child_id_b: 1.75}

        metric = self._make_metric(
            organization,
            workspace,
            composite_template,
            dataset,
            composite_weight_overrides=overrides,
        )
        metric.refresh_from_db()
        assert metric.composite_weight_overrides == overrides

    def test_allowed_on_single_metric_but_ignored_semantically(
        self, organization, workspace, single_template, dataset
    ):
        """Schema permits the field on single evals; runners ignore it."""
        metric = self._make_metric(
            organization,
            workspace,
            single_template,
            dataset,
            composite_weight_overrides={"irrelevant": 1.0},
        )
        assert metric.composite_weight_overrides == {"irrelevant": 1.0}
