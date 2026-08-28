# Generated migration for dataset optimization fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('model_hub', '0050_alter_feedback_options_feedback_organization_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='optimizedataset',
            name='optimizer_algorithm',
            field=models.CharField(
                blank=True,
                choices=[
                    ('random_search', 'Random Search'),
                    ('bayesian', 'Bayesian'),
                    ('metaprompt', 'Metaprompt'),
                    ('protegi', 'Protegi'),
                    ('promptwizard', 'PromptWizard'),
                    ('gepa', 'GEPA'),
                ],
                max_length=50,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='optimizedataset',
            name='optimizer_config',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Optimizer-specific configuration (num_trials, etc.)',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='optimizedataset',
            name='optimizer_model',
            field=models.ForeignKey(
                blank=True,
                help_text='Model used for optimization (separate from eval model)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='optimizer_runs',
                to='model_hub.aimodel',
            ),
        ),
        migrations.AddField(
            model_name='optimizedataset',
            name='column',
            field=models.ForeignKey(
                blank=True,
                help_text='Column being optimized',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='optimization_runs',
                to='model_hub.column',
            ),
        ),
        migrations.AddField(
            model_name='optimizedataset',
            name='error_message',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='optimizedataset',
            name='best_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='optimizedataset',
            name='baseline_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='optimizedataset',
            name='user_eval_template_ids',
            field=models.ManyToManyField(
                blank=True,
                help_text='Evaluation templates to optimize for',
                related_name='dataset_optimization_runs',
                to='model_hub.userevalmetric',
            ),
        ),
    ]
