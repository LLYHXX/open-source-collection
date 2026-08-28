"""
Migration script: Backfill eval_type and output_type_normalized on EvalTemplate.

Maps each EvalTemplate's config.eval_type_id to the correct eval_type
(agent, llm, code) and normalizes the output_type.

Usage:
    # Dry run (preview changes, no writes):
    python manage.py runscript evaluations.scripts.migrate_eval_types -- --dry-run

    # Execute:
    python manage.py runscript evaluations.scripts.migrate_eval_types

    # Or run directly:
    python manage.py shell -c "from evaluations.scripts.migrate_eval_types import run; run()"
"""

import structlog
from django.db import transaction

logger = structlog.get_logger(__name__)

# ============================================================================
# eval_type_id → eval_type mapping
# ============================================================================

# Agent: Uses Falcon AI AgentLoop for multi-turn reasoning
AGENT_TYPES = {
    "AgentEvaluator",
}

# Code: Deterministic / function-based evaluators — no LLM call
CODE_TYPES = {
    "FunctionEvaluator",
    "CustomCodeEval",
    # Function wrappers (all deterministic, regex, string checks, etc.)
    "Contains",
    "ContainsAll",
    "ContainsAny",
    "ContainsNone",
    "ContainsJson",
    "ContainsEmail",
    "ContainsLink",
    "ContainsValidLink",
    "IsJson",
    "IsEmail",
    "NoInvalidLinks",
    "Equals",
    "StartsWith",
    "EndsWith",
    "LengthLessThan",
    "LengthGreaterThan",
    "LengthBetween",
    "OneLine",
    "Regex",
    "JsonSchema",
    "JsonValidation",
    "ApiCall",
    # Similarity / scoring functions (no LLM)
    "BleuScore",
    "RougeScore",
    "FidScore",
    "ClipScore",
    "RecallScore",
    "RecallAtK",
    "PrecisionAtK",
    "NdcgAtK",
    "Mrr",
    "HitRate",
    "LevenshteinSimilarity",
    "NumericSimilarity",
    "EmbeddingSimilarity",
    "SemanticListContains",
    "AnswerSimilarity",
}

# LLM: Everything else — uses an LLM call (custom prompt, deterministic with LLM, etc.)
LLM_TYPES = {
    "CustomPromptEvaluator",
    "DeterministicEvaluator",  # FutureAGI — uses Turing LLM
    "RankingEvaluator",  # FutureAGI — uses Turing LLM
    "GroundedEvaluator",
    "Groundedness",
    "LlmEvaluator",
    "BaseEvaluator",
}


def get_eval_type(eval_type_id: str) -> str:
    """Map eval_type_id to eval_type (agent, llm, code)."""
    if eval_type_id in AGENT_TYPES:
        return "agent"
    if eval_type_id in CODE_TYPES:
        return "code"
    if eval_type_id in LLM_TYPES:
        return "llm"
    # Default: if it has a function_eval flag, it's code
    return "llm"


# ============================================================================
# output type normalization
# ============================================================================

OUTPUT_TYPE_MAP = {
    "Pass/Fail": "pass_fail",
    "score": "percentage",
    "numeric": "percentage",
    "reason": "percentage",
    "choices": "deterministic",
    "": "percentage",
}


def get_output_type_normalized(config: dict, eval_type_id: str) -> str:
    """Derive output_type_normalized from config.output and eval_type_id."""
    output = config.get("output", "score")

    # Function evals are always deterministic
    if eval_type_id in CODE_TYPES:
        if output == "Pass/Fail":
            return "pass_fail"
        return "deterministic"

    return OUTPUT_TYPE_MAP.get(output, "percentage")


# ============================================================================
# Main migration
# ============================================================================


def run(*args):
    """
    Backfill eval_type and output_type_normalized on all EvalTemplate records.
    Pass --dry-run to preview without writing.
    """
    dry_run = "--dry-run" in args

    from model_hub.models.evals_metric import EvalTemplate

    templates = EvalTemplate.no_workspace_objects.filter(deleted=False)
    total = templates.count()
    print(f"\nFound {total} eval templates to process")

    stats = {
        "agent": 0,
        "llm": 0,
        "code": 0,
        "skipped_no_type_id": 0,
        "already_correct": 0,
        "updated": 0,
    }

    updates = []

    for tmpl in templates.iterator():
        config = tmpl.config or {}
        eval_type_id = config.get("eval_type_id", "")

        if not eval_type_id:
            stats["skipped_no_type_id"] += 1
            continue

        # Compute new values
        new_eval_type = get_eval_type(eval_type_id)
        new_output_normalized = get_output_type_normalized(config, eval_type_id)

        # Check if function_eval flag overrides to code
        if config.get("function_eval") and new_eval_type != "agent":
            new_eval_type = "code"

        # Never downgrade: if eval_type was manually set to 'agent', keep it
        if tmpl.eval_type == "agent" and new_eval_type != "agent":
            new_eval_type = "agent"

        # Check if already correct
        if (
            tmpl.eval_type == new_eval_type
            and tmpl.output_type_normalized == new_output_normalized
        ):
            stats["already_correct"] += 1
            continue

        stats[new_eval_type] += 1
        stats["updated"] += 1

        if dry_run:
            print(
                f"  [{tmpl.id}] {tmpl.name}: "
                f"eval_type {tmpl.eval_type!r} → {new_eval_type!r}, "
                f"output_normalized {tmpl.output_type_normalized!r} → {new_output_normalized!r} "
                f"(eval_type_id={eval_type_id})"
            )
        else:
            tmpl.eval_type = new_eval_type
            tmpl.output_type_normalized = new_output_normalized
            updates.append(tmpl)

    if not dry_run and updates:
        # Bulk update in batches to avoid memory issues
        batch_size = 500
        with transaction.atomic():
            for i in range(0, len(updates), batch_size):
                batch = updates[i : i + batch_size]
                EvalTemplate.no_workspace_objects.bulk_update(
                    batch,
                    ["eval_type", "output_type_normalized"],
                    batch_size=batch_size,
                )
        print(f"\nUpdated {len(updates)} templates")

    print(f"\n--- Stats ---")
    print(f"  Total templates:    {total}")
    print(f"  Already correct:    {stats['already_correct']}")
    print(f"  Updated:            {stats['updated']}")
    print(f"    → agent:          {stats['agent']}")
    print(f"    → llm:            {stats['llm']}")
    print(f"    → code:           {stats['code']}")
    print(f"  Skipped (no type):  {stats['skipped_no_type_id']}")

    if dry_run:
        print(f"\n  *** DRY RUN — no changes written ***")
