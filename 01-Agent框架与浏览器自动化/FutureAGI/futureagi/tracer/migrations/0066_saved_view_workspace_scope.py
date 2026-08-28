import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracer", "0065_imagine_analysis"),
    ]

    operations = [
        # Make project nullable so saved views can be workspace-scoped
        migrations.AlterField(
            model_name="savedview",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="saved_views",
                to="tracer.project",
            ),
        ),
        # Add "users" to tab_type choices
        migrations.AlterField(
            model_name="savedview",
            name="tab_type",
            field=models.CharField(
                choices=[
                    ("traces", "Traces"),
                    ("spans", "Spans"),
                    ("voice", "Voice"),
                    ("imagine", "Imagine"),
                    ("users", "Users"),
                ],
                max_length=20,
            ),
        ),
        # Replace the old project-scoped uniqueness with a partial index
        # that only applies when project is not null.
        migrations.RemoveConstraint(
            model_name="savedview",
            name="unique_saved_view_name_per_user_project",
        ),
        migrations.AddConstraint(
            model_name="savedview",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ("deleted", False), ("project__isnull", False)
                ),
                fields=("project", "created_by", "name"),
                name="unique_saved_view_name_per_user_project",
            ),
        ),
        # New workspace-scoped uniqueness when project is null.
        migrations.AddConstraint(
            model_name="savedview",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ("deleted", False), ("project__isnull", True)
                ),
                fields=("workspace", "created_by", "tab_type", "name"),
                name="unique_saved_view_name_per_user_workspace",
            ),
        ),
        migrations.AddIndex(
            model_name="savedview",
            index=models.Index(
                fields=["workspace", "created_by", "tab_type"],
                name="tracer_save_workspa_0c1ef5_idx",
            ),
        ),
    ]
