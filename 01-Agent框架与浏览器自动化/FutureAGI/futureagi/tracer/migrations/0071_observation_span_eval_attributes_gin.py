from django.db import migrations


class Migration(migrations.Migration):
    """Add GIN index on `eval_attributes` for JSONB containment queries.

    The simulate CallExecution → Trace lookup uses
    ``eval_attributes @> '{"fi.simulator.call_execution_id": "..."}'``.
    Without this index the planner falls back to a sequential scan over
    the whole table (measured: 20s on ~430k rows). ``jsonb_path_ops``
    is the containment-optimized opclass — smaller and faster than the
    default ``jsonb_ops`` when we only ever use ``@>``.
    """

    atomic = False

    dependencies = [
        ("tracer", "0070_merge_20260417_1113"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
                "tracer_obse_eval_attr_gin "
                "ON public.tracer_observation_span "
                "USING gin (eval_attributes jsonb_path_ops);"
            ),
            reverse_sql=(
                "DROP INDEX CONCURRENTLY IF EXISTS tracer_obse_eval_attr_gin;"
            ),
        ),
    ]
