"""
Pre-migration verification: checks ALL existing experiments for data integrity.

This version works on systems where the experiment FK migration (0057) has NOT
been applied yet.  It uses the M2M relationship instead of the FK.

Run BEFORE applying migrations:
    python manage.py verify_experiment_data_premigration

Exit code 0 if no errors, 1 if errors found.
"""

import sys

from django.core.management.base import BaseCommand

from model_hub.models.develop_dataset import Dataset
from model_hub.models.evals_metric import UserEvalMetric
from model_hub.models.experiments import (
    ExperimentDatasetTable,
    ExperimentsTable,
)


class Command(BaseCommand):
    help = "Verify integrity of all existing experiments before migration (pre-migration schema)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Attempt to fix minor issues (e.g., orphaned EDT records).",
        )

    def handle(self, *args, **options):
        fix = options["fix"]
        errors = []
        warnings = []

        experiments = ExperimentsTable.all_objects.filter(deleted=False)
        total = experiments.count()
        self.stdout.write(f"Checking {total} experiments...")

        for exp in experiments.iterator(chunk_size=500):
            exp_errors, exp_warnings = self._check_experiment(exp)
            errors.extend(exp_errors)
            warnings.extend(exp_warnings)

        # Check orphaned ExperimentDatasetTable records
        orphaned = self._check_orphaned_edts(fix)
        warnings.extend(orphaned)

        self.stdout.write("")
        if warnings:
            self.stdout.write(self.style.WARNING(f"Warnings: {len(warnings)}"))
            for w in warnings:
                self.stdout.write(f"  WARN: {w}")

        if errors:
            self.stdout.write(self.style.ERROR(f"Errors: {len(errors)}"))
            for e in errors:
                self.stdout.write(f"  ERROR: {e}")
            sys.exit(1)
        else:
            self.stdout.write(
                self.style.SUCCESS(f"All {total} experiments passed verification.")
            )
            sys.exit(0)

    def _check_experiment(self, exp):
        errors = []
        warnings = []
        exp_id = str(exp.id)

        # 1. Check prompt_config is a valid list
        pc = exp.prompt_config
        if not isinstance(pc, list):
            errors.append(
                f"Experiment {exp_id}: prompt_config is not a list (got {type(pc).__name__})"
            )
            return errors, warnings

        if not pc:
            warnings.append(f"Experiment {exp_id}: prompt_config is empty")
            return errors, warnings

        # 2. Check each entry has required keys
        for i, entry in enumerate(pc):
            if not isinstance(entry, dict):
                errors.append(f"Experiment {exp_id}: prompt_config[{i}] is not a dict")
                continue

            if "messages" not in entry:
                errors.append(
                    f"Experiment {exp_id}: prompt_config[{i}] missing 'messages'"
                )
            elif not isinstance(entry["messages"], list):
                errors.append(
                    f"Experiment {exp_id}: prompt_config[{i}].messages is not a list"
                )

            if "model" not in entry:
                errors.append(
                    f"Experiment {exp_id}: prompt_config[{i}] missing 'model'"
                )
            elif not isinstance(entry["model"], list):
                errors.append(
                    f"Experiment {exp_id}: prompt_config[{i}].model is not a list"
                )
            elif not entry["model"]:
                errors.append(
                    f"Experiment {exp_id}: prompt_config[{i}].model is empty list"
                )

            if "name" not in entry:
                warnings.append(
                    f"Experiment {exp_id}: prompt_config[{i}] missing 'name'"
                )

        # 3. Check referenced dataset exists
        try:
            dataset = exp.dataset
            if not dataset:
                errors.append(f"Experiment {exp_id}: dataset is null")
            elif dataset.deleted:
                warnings.append(
                    f"Experiment {exp_id}: dataset {dataset.id} is soft-deleted"
                )
        except Dataset.DoesNotExist:
            errors.append(
                f"Experiment {exp_id}: dataset FK references non-existent record"
            )

        # 4. Check user_eval_template_ids reference existing records
        eval_ids = list(exp.user_eval_template_ids.values_list("id", flat=True))
        if eval_ids:
            existing = set(
                UserEvalMetric.all_objects.filter(id__in=eval_ids).values_list(
                    "id", flat=True
                )
            )
            missing = set(eval_ids) - existing
            if missing:
                warnings.append(
                    f"Experiment {exp_id}: user_eval_template_ids references "
                    f"{len(missing)} non-existent UserEvalMetric records"
                )

        # 5. Check ExperimentDatasetTable records have valid columns
        # Use M2M relationship (works pre-migration, no FK needed)
        edts = exp.experiments_datasets.filter(deleted=False)
        for edt in edts:
            col_count = edt.columns.filter(deleted=False).count()
            if col_count == 0:
                warnings.append(
                    f"Experiment {exp_id}: ExperimentDatasetTable {edt.id} ('{edt.name}') has no columns"
                )

        return errors, warnings

    def _check_orphaned_edts(self, fix=False):
        warnings = []

        # EDT records with no M2M link to any experiment
        orphaned_edts = ExperimentDatasetTable.all_objects.filter(
            experiments_datasets_created__isnull=True,
            deleted=False,
        )
        count = orphaned_edts.count()
        if count > 0:
            warnings.append(
                f"Found {count} orphaned ExperimentDatasetTable records (no experiment link)"
            )
            if fix:
                orphaned_edts.update(deleted=True)
                warnings.append(f"  -> Soft-deleted {count} orphaned EDT records")

        return warnings
