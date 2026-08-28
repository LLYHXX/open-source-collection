# Generated migration for adding indexes on prompt_label field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracer', '0031_observationspan_prompt_label'),
    ]
    
    # IMPORTANT: atomic=False is required for CREATE INDEX CONCURRENTLY
    # This allows the indexes to be created without blocking table writes
    atomic = False

    operations = [
        # Add index on prompt_label_id for faster lookups
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_observation_span_prompt_label 
                ON tracer_observation_span(prompt_label_id) 
                WHERE prompt_label_id IS NOT NULL;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_observation_span_prompt_label;
            """
        ),
        
        # Add composite index on (prompt_version_id, prompt_label_id) for GROUP BY queries
        # This is crucial for the CTE-based prompt metrics query performance
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_observation_span_pv_pl 
                ON tracer_observation_span(prompt_version_id, prompt_label_id) 
                WHERE prompt_version_id IS NOT NULL AND prompt_label_id IS NOT NULL;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_observation_span_pv_pl;
            """
        ),
        
        # Add composite index including created_at for time-based filtering
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_observation_span_pv_pl_created 
                ON tracer_observation_span(prompt_version_id, prompt_label_id, created_at DESC) 
                WHERE prompt_version_id IS NOT NULL AND prompt_label_id IS NOT NULL;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_observation_span_pv_pl_created;
            """
        ),
    ]

