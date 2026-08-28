# Generated manually for graph query optimization
# This migration adds composite indexes to optimize graph data queries
# handling 10M+ records with efficient filtering and aggregation

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracer', '0035_merge_20251111_1229'),
    ]

    operations = [
        # =====================================================================
        # EvalLogger Indexes for Graph Queries
        # =====================================================================
        # These indexes optimize queries in graphs_optimized.py that filter by:
        # - custom_eval_config + created_at (time-series aggregation)
        # - observation_span + custom_eval_config + created_at (span-based eval graphs)
        # - trace + custom_eval_config + created_at (trace-based eval graphs)
        
        migrations.AddIndex(
            model_name='evallogger',
            index=models.Index(
                fields=['custom_eval_config', 'created_at'],
                name='evallog_config_time_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='evallogger',
            index=models.Index(
                fields=['observation_span', 'custom_eval_config', 'created_at'],
                name='evallog_span_cfg_time_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='evallogger',
            index=models.Index(
                fields=['trace', 'custom_eval_config', 'created_at'],
                name='evallog_trace_cfg_time_idx',
            ),
        ),
        
        # =====================================================================
        # ObservationSpan Indexes for System Metrics
        # =====================================================================
        # These indexes optimize system metric queries (latency, tokens, cost)
        # that aggregate by project + time with metric values
        
        migrations.AddIndex(
            model_name='observationspan',
            index=models.Index(
                fields=['project', 'created_at', 'latency_ms'],
                name='span_proj_time_lat_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='observationspan',
            index=models.Index(
                fields=['project', 'created_at', 'total_tokens'],
                name='span_proj_time_tok_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='observationspan',
            index=models.Index(
                fields=['project', 'created_at', 'cost'],
                name='span_proj_time_cost_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='observationspan',
            index=models.Index(
                fields=['trace', 'created_at'],
                name='span_trace_time_idx',
            ),
        ),
        
        # =====================================================================
        # TraceAnnotation Indexes for Annotation Graphs
        # =====================================================================
        # These indexes optimize annotation graph queries that filter by:
        # - annotation_label + created_at (base aggregation)
        # - observation_span + annotation_label + created_at (span-based annotations)
        # - annotation_label + created_at + value fields (for aggregations with values)
        
        migrations.AddIndex(
            model_name='traceannotation',
            index=models.Index(
                fields=['annotation_label', 'created_at', 'annotation_value_float'],
                name='annot_label_time_float_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='traceannotation',
            index=models.Index(
                fields=['annotation_label', 'created_at', 'annotation_value_bool'],
                name='annot_label_time_bool_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='traceannotation',
            index=models.Index(
                fields=['observation_span', 'annotation_label', 'created_at'],
                name='annot_span_label_time_idx',
            ),
        ),
    ]

