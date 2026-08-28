# Generated manually to add composite index on auto-generated through table

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('model_hub', '0036_merge_20251001_0933'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS idx_promptversion_labels_composite 
                ON model_hub_promptversion_labels (promptlabel_id, promptversion_id);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_promptversion_labels_composite;
            """
        ),
    ]

