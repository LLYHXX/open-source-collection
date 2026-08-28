# Generated for composite eval wiring (Phase 7 — wiring plan, Phase A)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("model_hub", "0084_composite_child_axis"),
    ]

    operations = [
        migrations.AddField(
            model_name="evaluation",
            name="parent_evaluation",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "When this row is a child result inside a composite eval run, "
                    "points to the aggregate (parent) Evaluation row. Null for single "
                    "evals and for composites with aggregation_enabled=False."
                ),
                null=True,
                on_delete=models.deletion.CASCADE,
                related_name="child_evaluations",
                to="model_hub.evaluation",
            ),
        ),
        migrations.AddIndex(
            model_name="evaluation",
            index=models.Index(
                fields=["parent_evaluation"],
                name="model_hub_e_parent__90a066_idx",
            ),
        ),
        migrations.AddField(
            model_name="userevalmetric",
            name="composite_weight_overrides",
            field=models.JSONField(
                blank=True,
                default=None,
                help_text=(
                    "Per-binding weight overrides for composite child evals. "
                    'Maps {"<child_template_id>": <weight float>}. '
                    "When null, runners fall back to CompositeEvalChild.weight on the template. "
                    "Ignored for single evals."
                ),
                null=True,
            ),
        ),
    ]
