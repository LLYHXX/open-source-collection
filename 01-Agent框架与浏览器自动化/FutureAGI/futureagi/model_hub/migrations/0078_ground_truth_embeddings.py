# Phase 9: Ground Truth enhancements — add new fields + embedding table

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("model_hub", "0077_add_eval_type"),
    ]

    operations = [
        # --- Add new fields to existing EvalGroundTruth ---
        migrations.AddField(
            model_name="evalgroundtruth",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="evalgroundtruth",
            name="role_mapping",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="evalgroundtruth",
            name="embedding_status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")],
                default="pending", max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="evalgroundtruth",
            name="embedding_model",
            field=models.CharField(default="text-embedding-3-small", max_length=100),
        ),
        migrations.AddField(
            model_name="evalgroundtruth",
            name="embedded_row_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="evalgroundtruth",
            name="storage_type",
            field=models.CharField(
                choices=[("db", "Database"), ("s3", "S3")],
                default="db", max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="evalgroundtruth",
            name="s3_key",
            field=models.CharField(blank=True, default="", max_length=1000),
        ),
        # --- Create EvalGroundTruthEmbedding model ---
        migrations.CreateModel(
            name="EvalGroundTruthEmbedding",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("row_index", models.IntegerField()),
                ("text_content", models.TextField()),
                ("embedding", models.JSONField()),
                ("row_data", models.JSONField()),
                (
                    "ground_truth",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="embeddings",
                        to="model_hub.evalgroundtruth",
                    ),
                ),
            ],
            options={
                "db_table": "model_hub_eval_ground_truth_embedding",
                "ordering": ["row_index"],
                "unique_together": {("ground_truth", "row_index")},
                "indexes": [
                    models.Index(fields=["ground_truth", "row_index"], name="model_hub_e_ground__emb_idx"),
                ],
            },
        ),
    ]
