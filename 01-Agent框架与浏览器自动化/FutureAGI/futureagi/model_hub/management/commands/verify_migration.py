"""
Post-migration verification: checks that all experiments were correctly migrated.

Run AFTER migrate_experiment_prompts:
    python manage.py verify_migration

Exit code 0 if no errors, 1 if errors found.
"""

import sys

from django.core.management.base import BaseCommand
from tqdm import tqdm

from model_hub.models.experiments import (
    ExperimentPromptConfig,
    ExperimentsTable,
)


class Command(BaseCommand):
    help = "Verify that all experiments were correctly migrated to the new schema."

    def handle(self, *args, **options):
        errors = []
        warnings = []

        experiments = ExperimentsTable.all_objects.filter(deleted=False)
        total = experiments.count()
        self.stdout.write(f"Verifying {total} experiments...")

        for exp in tqdm(
            experiments.iterator(chunk_size=500),
            total=total,
            desc="Verifying migration",
            unit="exp",
        ):
            exp_errors, exp_warnings = self._verify_experiment(exp)
            errors.extend(exp_errors)
            warnings.extend(exp_warnings)

        self.stdout.write("")
        if warnings:
            self.stdout.write(self.style.WARNING(f"Warnings: {len(warnings)}"))
            for w in warnings[:50]:  # Cap output
                self.stdout.write(f"  WARN: {w}")
            if len(warnings) > 50:
                self.stdout.write(f"  ... and {len(warnings) - 50} more")

        if errors:
            self.stdout.write(self.style.ERROR(f"Errors: {len(errors)}"))
            for e in errors[:50]:
                self.stdout.write(f"  ERROR: {e}")
            if len(errors) > 50:
                self.stdout.write(f"  ... and {len(errors) - 50} more")
            sys.exit(1)
        else:
            self.stdout.write(
                self.style.SUCCESS(f"All {total} experiments verified successfully.")
            )
            sys.exit(0)

    def _verify_experiment(self, exp):
        errors = []
        warnings = []
        exp_id = str(exp.id)

        # 1. experiment_type must be set
        if exp.experiment_type not in ("llm", "tts", "stt", "image"):
            errors.append(
                f"Experiment {exp_id}: invalid experiment_type '{exp.experiment_type}'"
            )

        # 2. Check EPC count matches expected count from prompt_config
        prompt_config = exp.prompt_config
        if not isinstance(prompt_config, list) or not prompt_config:
            # Experiments with empty prompt_config might be valid (e.g., agent-only)
            warnings.append(f"Experiment {exp_id}: empty prompt_config")
            return errors, warnings

        expected_epc_count = sum(
            len(entry.get("model", []))
            for entry in prompt_config
            if isinstance(entry, dict)
        )

        actual_epcs = list(
            ExperimentPromptConfig.all_objects.filter(
                experiment_dataset__experiment=exp, deleted=False
            ).select_related("prompt_version")
        )
        actual_count = len(actual_epcs)

        if actual_count == 0:
            errors.append(
                f"Experiment {exp_id}: no EPCs found (expected {expected_epc_count})"
            )
            return errors, warnings

        if actual_count != expected_epc_count:
            warnings.append(
                f"Experiment {exp_id}: EPC count mismatch "
                f"(expected {expected_epc_count}, got {actual_count})"
            )

        # 3. Verify each EPC based on experiment_type
        for epc in actual_epcs:
            epc_id = str(epc.id)

            # Model must be a non-empty string
            if not epc.model or not epc.model.strip():
                errors.append(f"EPC {epc_id}: model is empty")

            if exp.experiment_type == "llm":
                # LLM: must have prompt_template and prompt_version, messages should be null
                if not epc.prompt_template_id:
                    errors.append(
                        f"EPC {epc_id}: LLM experiment but prompt_template is null"
                    )
                if not epc.prompt_version_id:
                    errors.append(
                        f"EPC {epc_id}: LLM experiment but prompt_version is null"
                    )
                if epc.messages is not None:
                    warnings.append(
                        f"EPC {epc_id}: LLM experiment but messages is not null"
                    )

                # Verify prompt_version has valid snapshot
                if epc.prompt_version_id:
                    try:
                        pv = epc.prompt_version
                        if not pv.prompt_config_snapshot:
                            errors.append(
                                f"EPC {epc_id}: prompt_version {pv.id} has empty prompt_config_snapshot"
                            )
                    except Exception:
                        errors.append(
                            f"EPC {epc_id}: prompt_version FK references non-existent record"
                        )

            else:
                # TTS/STT/Image: prompt_template/prompt_version must be null, messages must be set
                if epc.prompt_template_id:
                    errors.append(
                        f"EPC {epc_id}: {exp.experiment_type} experiment but prompt_template is set"
                    )
                if epc.prompt_version_id:
                    errors.append(
                        f"EPC {epc_id}: {exp.experiment_type} experiment but prompt_version is set"
                    )
                if not epc.messages:
                    errors.append(
                        f"EPC {epc_id}: {exp.experiment_type} experiment but messages is empty"
                    )

                # STT-specific: voice_input_column should be set
                if exp.experiment_type == "stt" and not epc.voice_input_column_id:
                    warnings.append(
                        f"EPC {epc_id}: STT experiment but voice_input_column is not set"
                    )

        # 4. Verify EPCs sharing the same prompt reference the same PromptTemplate/PromptVersion
        if exp.experiment_type == "llm":
            self._verify_shared_templates(exp, actual_epcs, errors, warnings)

        return errors, warnings

    def _verify_shared_templates(self, exp, epcs, errors, warnings):
        """Verify that EPCs from the same prompt_config entry share PromptTemplate/PromptVersion."""
        # Group EPCs by prompt_template
        by_template = {}
        for epc in epcs:
            if epc.prompt_template_id:
                key = str(epc.prompt_template_id)
                if key not in by_template:
                    by_template[key] = []
                by_template[key].append(epc)

        # Each group should share the same prompt_version
        for template_id, group in by_template.items():
            version_ids = {str(epc.prompt_version_id) for epc in group}
            if len(version_ids) > 1:
                warnings.append(
                    f"Experiment {exp.id}: EPCs with template {template_id} "
                    f"have {len(version_ids)} different prompt_versions"
                )
