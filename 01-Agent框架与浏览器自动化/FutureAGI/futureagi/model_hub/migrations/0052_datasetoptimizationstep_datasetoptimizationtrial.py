# Generated migration for DatasetOptimizationStep and DatasetOptimizationTrial

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('model_hub', '0051_optimizedataset_optimizer_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='DatasetOptimizationStep',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('step_number', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('running', 'Running'),
                        ('completed', 'Completed'),
                        ('failed', 'Failed'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('metadata', models.JSONField(blank=True, null=True)),
                ('optimization_run', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='steps',
                    to='model_hub.optimizedataset',
                )),
            ],
            options={
                'db_table': 'dataset_optimization_step',
                'unique_together': {('optimization_run', 'step_number')},
            },
        ),
        migrations.CreateModel(
            name='DatasetOptimizationTrial',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('trial_number', models.IntegerField()),
                ('is_baseline', models.BooleanField(default=False)),
                ('prompt', models.TextField(blank=True, null=True)),
                ('average_score', models.FloatField()),
                ('metadata', models.JSONField(blank=True, null=True)),
                ('optimization_run', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='trials',
                    to='model_hub.optimizedataset',
                )),
            ],
            options={
                'db_table': 'dataset_optimization_trial',
                'ordering': ['trial_number'],
                'unique_together': {('optimization_run', 'trial_number')},
            },
        ),
    ]
