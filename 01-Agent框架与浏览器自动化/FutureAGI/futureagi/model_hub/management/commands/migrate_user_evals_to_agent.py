"""
Migration: flip LLM-type evals over to the new Agent type.

Selects EvalTemplate rows where:
    eval_type  = "llm"
    config.eval_type_id = "CustomPromptEvaluator"
    owner      = "user"                (default)
    owner      in ("user", "system")   (with --include-system)

For each row:
    eval_type           -> "agent"
    config.eval_type_id -> "AgentEvaluator"
    config.agent_mode   -> "quick"  (closest behavior to the old prompt evaluator)
    config.tools        -> {"internet": <existing check_internet>, "connectors": []}
    config.knowledge_bases -> []
    config.data_injection  -> {"variables_only": True}
    config.summary      -> {"type": "concise"}

rule_prompt / model / output_type / choice_scores / pass_threshold are left alone.

This is NOT a Django data migration on purpose — runtime behavior changes when
CustomPromptEvaluator is swapped for AgentEvaluator (different prompt shell,
agent loop vs single-shot LLM call), so the flip is opt-in per environment.

System evals: the canonical source of truth is the YAML tree under
`model_hub/system_evals/`, applied by `seed_system_evals`. Prefer re-running
that command when possible. `--include-system` is for environments where the
seeder is behind and stale system evals are still routing to
CustomPromptEvaluator at runtime.

Run it yourself:
    python manage.py migrate_user_evals_to_agent --dry-run
    python manage.py migrate_user_evals_to_agent --org-id <uuid>
    python manage.py migrate_user_evals_to_agent --include-system
    python manage.py migrate_user_evals_to_agent            # full rollout (users only)

Idempotent: already-agent rows are excluded by the filter.
"""

import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from model_hub.models.choices import OwnerChoices
from model_hub.models.evals_metric import EvalTemplate, EvalTemplateVersion

logger = logging.getLogger(__name__)


def _build_agent_config(old_config: dict) -> dict:
    """Rewrite a CustomPromptEvaluator config as an AgentEvaluator config.

    Agent-specific fields that are already populated on the source row
    (knowledge_bases, tools, data_injection, summary) are preserved — this
    migration never silently drops wiring the user set up.
    """
    new_config = dict(old_config or {})
    new_config["eval_type_id"] = "AgentEvaluator"
    new_config["agent_mode"] = new_config.get("agent_mode") or "quick"

    existing_tools = new_config.get("tools")
    if not existing_tools:
        new_config["tools"] = {
            "internet": bool(new_config.get("check_internet", False)),
            "connectors": [],
        }

    if not new_config.get("knowledge_bases"):
        # preserve a legacy single-KB pointer if one is there
        legacy_kb = new_config.get("knowledge_base_id")
        new_config["knowledge_bases"] = [legacy_kb] if legacy_kb else []

    if not new_config.get("data_injection"):
        new_config["data_injection"] = {"variables_only": True}

    if not new_config.get("summary"):
        new_config["summary"] = {"type": "concise"}

    # rule_prompt is already populated by create-v2. If an older row only has
    # system_prompt, promote it so AgentEvaluator can find the criteria.
    if not new_config.get("rule_prompt") and new_config.get("system_prompt"):
        new_config["rule_prompt"] = new_config["system_prompt"]
    return new_config


class Command(BaseCommand):
    help = "Flip user-created LLM evals to Agent type."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without writing.",
        )
        parser.add_argument(
            "--org-id",
            type=str,
            default=None,
            help="Restrict migration to a single organization (UUID).",
        )
        parser.add_argument(
            "--include-system",
            action="store_true",
            help=(
                "Also flip system-owned evals still on CustomPromptEvaluator. "
                "Prefer running `seed_system_evals` if the YAML tree is up to date."
            ),
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Rows committed per transaction (default 100).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        org_id = options["org_id"]
        batch_size = options["batch_size"]
        include_system = options["include_system"]

        owners = [OwnerChoices.USER.value]
        if include_system:
            owners.append(OwnerChoices.SYSTEM.value)

        qs = EvalTemplate.no_workspace_objects.filter(
            owner__in=owners,
            eval_type="llm",
            config__eval_type_id="CustomPromptEvaluator",
            deleted=False,
        ).order_by("id")

        if org_id:
            qs = qs.filter(organization_id=org_id)

        total = qs.count()
        self.stdout.write(f"Candidates: {total}")
        if total == 0:
            return

        updated = 0
        skipped = 0
        batch: list[EvalTemplate] = []

        def _flush(batch_rows: list[EvalTemplate]) -> int:
            if not batch_rows:
                return 0
            if dry_run:
                return len(batch_rows)
            with transaction.atomic():
                for row in batch_rows:
                    row.save(update_fields=["eval_type", "config", "updated_at"])
                    # Keep the active version snapshot in sync with the
                    # flipped template. Historical (non-default) versions
                    # are left alone as audit.
                    default_version = EvalTemplateVersion.objects.filter(
                        eval_template=row, is_default=True
                    ).first()
                    if default_version is not None:
                        default_version.config_snapshot = row.config
                        default_version.save(
                            update_fields=["config_snapshot", "updated_at"]
                        )
            return len(batch_rows)

        for template in qs.iterator(chunk_size=batch_size):
            try:
                template.eval_type = "agent"
                template.config = _build_agent_config(template.config or {})
                batch.append(template)
            except Exception as e:
                skipped += 1
                logger.warning(
                    "migrate_user_evals_to_agent skipped id=%s err=%s",
                    template.id,
                    e,
                )
                continue

            if len(batch) >= batch_size:
                updated += _flush(batch)
                batch = []

        updated += _flush(batch)

        verb = "Would update" if dry_run else "Updated"
        self.stdout.write(
            f"{verb}: {updated} eval(s). Skipped: {skipped}. Candidates: {total}."
        )
