from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracer", "0066_saved_view_workspace_scope"),
    ]

    operations = [
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
                    ("user_detail", "User Detail"),
                ],
                max_length=20,
            ),
        ),
    ]
