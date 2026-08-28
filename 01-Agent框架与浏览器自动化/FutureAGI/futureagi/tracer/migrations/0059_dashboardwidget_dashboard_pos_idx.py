# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracer", "0058_dashboard_models"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="dashboardwidget",
            index=models.Index(
                fields=["dashboard", "position"],
                name="tracer_widget_dashboard_pos_idx",
            ),
        ),
    ]
