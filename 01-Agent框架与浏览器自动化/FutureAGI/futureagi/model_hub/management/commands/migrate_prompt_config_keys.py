"""
Data migration (TH-4515): rename legacy camelCase keys → snake_case in stored prompt configs.

Targets JSON blobs that historically carried frontend camelCase form-state, including:
- PromptVersion.prompt_config_snapshot (prompt_config_snapshot.configuration)
- PromptBaseTemplate.prompt_config_snapshot
- RunPrompter.run_prompt_config
- Experiment V2 prompt/model config JSON fields (model_config/model_params/configuration/prompt_config)
- PendingRowTask.model_config and PendingRowTask.run_prompt_config

Rules:
- If both legacy and canonical keys exist, keep canonical and drop legacy.
- Idempotent: safe to re-run.

Usage:
  python manage.py migrate_prompt_config_keys --dry-run
  python manage.py migrate_prompt_config_keys --batch-size 1000
"""

from __future__ import annotations

from dataclasses import dataclass

from django.core.management.base import BaseCommand
from django.db import transaction

from model_hub.utils.prompt_config_key_renamer import rename_legacy_camelcase_keys


@dataclass(frozen=True)
class Target:
    model_label: str
    model: type
    field: str


class Command(BaseCommand):
    help = "Migrate legacy camelCase keys to canonical snake_case in prompt-related JSON fields."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be changed without writing to the DB.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Rows to bulk_update per batch (default: 1000).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Optional max rows per target (useful for staged rollouts).",
        )
        parser.add_argument(
            "--only-active",
            action="store_true",
            help="Only migrate non-deleted rows (uses the default manager).",
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]
        batch_size: int = options["batch_size"]
        limit: int | None = options["limit"]
        only_active: bool = options["only_active"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes will be made"))

        targets = self._get_targets()
        if not targets:
            self.stdout.write(self.style.ERROR("No targets found. Aborting."))
            return

        total_scanned = 0
        total_changed = 0
        total_updated = 0

        for target in targets:
            scanned, changed, updated = self._migrate_target(
                target=target,
                dry_run=dry_run,
                batch_size=batch_size,
                limit=limit,
                only_active=only_active,
            )
            total_scanned += scanned
            total_changed += changed
            total_updated += updated

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Migration complete"))
        self.stdout.write(f"Scanned: {total_scanned}")
        self.stdout.write(f"Would change: {total_changed}")
        if not dry_run:
            self.stdout.write(f"Updated: {total_updated}")

    def _get_targets(self) -> list[Target]:
        # Imports are local to avoid pulling in Django app models at import time.
        from model_hub.models.experiments import (
            ExperimentPromptConfig,
            ExperimentsTable,
            ExperimentDatasetTable,
            PendingRowTask,
        )
        from model_hub.models.prompt_base_template import PromptBaseTemplate
        from model_hub.models.run_prompt import PromptVersion, RunPrompter

        return [
            Target(
                model_label="model_hub.PromptVersion",
                model=PromptVersion,
                field="prompt_config_snapshot",
            ),
            Target(
                model_label="model_hub.PromptBaseTemplate",
                model=PromptBaseTemplate,
                field="prompt_config_snapshot",
            ),
            Target(
                model_label="model_hub.RunPrompter",
                model=RunPrompter,
                field="run_prompt_config",
            ),
            Target(
                model_label="model_hub.ExperimentsTable",
                model=ExperimentsTable,
                field="prompt_config",
            ),
            Target(
                model_label="model_hub.ExperimentDatasetTable",
                model=ExperimentDatasetTable,
                field="legacy_prompt_config",
            ),
            Target(
                model_label="model_hub.ExperimentPromptConfig",
                model=ExperimentPromptConfig,
                field="model_config",
            ),
            Target(
                model_label="model_hub.ExperimentPromptConfig",
                model=ExperimentPromptConfig,
                field="model_params",
            ),
            Target(
                model_label="model_hub.ExperimentPromptConfig",
                model=ExperimentPromptConfig,
                field="configuration",
            ),
            Target(
                model_label="model_hub.PendingRowTask",
                model=PendingRowTask,
                field="model_config",
            ),
            Target(
                model_label="model_hub.PendingRowTask",
                model=PendingRowTask,
                field="run_prompt_config",
            ),
        ]

    def _get_manager(self, model: type, only_active: bool):
        if only_active or not hasattr(model, "all_objects"):
            return model.objects
        return model.all_objects

    def _migrate_target(
        self,
        *,
        target: Target,
        dry_run: bool,
        batch_size: int,
        limit: int | None,
        only_active: bool,
    ) -> tuple[int, int, int]:
        manager = self._get_manager(target.model, only_active=only_active)
        qs = manager.all().only("id", target.field)
        if limit is not None:
            qs = qs[:limit]

        scanned = 0
        changed = 0
        updated = 0
        pending_updates = []

        self.stdout.write(
            f"{target.model_label}.{target.field}: scanning"
            + (f" (limit={limit})" if limit is not None else "")
            + (" (only_active)" if only_active else "")
        )

        for obj in qs.iterator(chunk_size=batch_size):
            scanned += 1
            original_value = getattr(obj, target.field, None)
            if original_value is None:
                continue

            new_value, did_change = rename_legacy_camelcase_keys(original_value)
            if not did_change:
                continue

            changed += 1
            if dry_run:
                continue

            setattr(obj, target.field, new_value)
            pending_updates.append(obj)

            if len(pending_updates) >= batch_size:
                updated += self._flush_updates(
                    manager=manager,
                    field=target.field,
                    objs=pending_updates,
                )
                pending_updates = []

        if pending_updates and not dry_run:
            updated += self._flush_updates(
                manager=manager, field=target.field, objs=pending_updates
            )

        self.stdout.write(
            f"{target.model_label}.{target.field}: scanned={scanned} changed={changed}"
            + (f" updated={updated}" if not dry_run else "")
        )
        return scanned, changed, updated

    def _flush_updates(self, *, manager, field: str, objs: list) -> int:
        with transaction.atomic():
            manager.bulk_update(objs, [field], batch_size=len(objs))
        return len(objs)
