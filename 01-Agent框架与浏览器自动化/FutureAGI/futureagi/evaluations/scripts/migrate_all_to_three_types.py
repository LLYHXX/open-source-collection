"""
Migration script: Convert ALL eval templates to one of 3 target types.

Target types:
  - AgentEvaluator     (eval_type="agent")  — multi-turn agent with tools
  - CustomPromptEvaluator (eval_type="llm") — LLM-as-a-judge
  - CustomCodeEval     (eval_type="code")   — user-written Python code

Mapping:
  → AgentEvaluator:
    - DeterministicEvaluator (criteria → rule_prompt)
    - RankingEvaluator (criteria → rule_prompt)
    - Already AgentEvaluator

  → CustomPromptEvaluator:
    - Groundedness, GroundedEvaluator
    - LlmEvaluator, BaseEvaluator
    - OutputEvaluator, PerplexityEvaluator, ChunkUtilization, ChunkAttribution
    - ConversationResolution, PiiDetection, AudioTranscriptionEvaluator
    - ImageInstructionEvaluator, ContextSimilarity
    - CustomPrompt (old name for same class)
    - Already CustomPromptEvaluator

  → CustomCodeEval:
    - All function wrappers (Contains, Regex, Equals, BleuScore, etc.)
    - Already CustomCodeEval

Usage:
    python manage.py shell -c "from evaluations.scripts.migrate_all_to_three_types import run; run('--dry-run')"
    python manage.py shell -c "from evaluations.scripts.migrate_all_to_three_types import run; run()"
"""

import copy

import structlog

logger = structlog.get_logger(__name__)

# ============================================================================
# Target mapping
# ============================================================================

TO_AGENT = {
    "DeterministicEvaluator",
    "RankingEvaluator",
}

# These all become AgentEvaluator — they're LLM-based system evals
# that ran through DeterministicEvaluator or had custom classes
TO_AGENT_LLM = {
    "Groundedness",  # LLM groundedness check → agent with groundedness prompt
    "LlmEvaluator",  # Generic LLM eval → agent
    "BaseEvaluator",  # Generic base → agent
    "OutputEvaluator",  # Output quality → agent
    "PerplexityEvaluator",  # Perplexity check → agent
    "ChunkUtilization",  # RAG chunk usage → agent
    "ChunkAttribution",  # RAG chunk attribution → agent
    "ConversationResolution",  # Conversation quality → agent
    "PiiDetection",  # PII detection → agent
    "AudioTranscriptionEvaluator",  # Audio transcription quality → agent
    "ImageInstructionEvaluator",  # Image instruction adherence → agent
    "ContextSimilarity",  # Context similarity → agent
    "CustomPrompt",  # Old name for CustomPromptEvaluator → agent
    "RankingEvaluator",  # Context ranking → agent
}

# These are pure similarity functions — no LLM needed → code
TO_CODE_SIMILARITY = {
    "GroundedEvaluator",  # Jaccard/Levenshtein/Cosine similarity → code
    "AnswerSimilarity",  # String similarity → code
}

TO_CODE = {
    "FunctionEvaluator",
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

ALREADY_TARGET = {"AgentEvaluator", "CustomPromptEvaluator", "CustomCodeEval"}


# ============================================================================
# System eval rule prompts — replicate the logic of each evaluator class
# ============================================================================

SYSTEM_EVAL_PROMPTS = {
    "Groundedness": (
        "You are evaluating whether a response is grounded in the provided context.\n\n"
        "For each sentence in the response, check if there is supporting evidence in the context.\n"
        "A sentence is 'grounded' if its key claims are supported by the context (minor rephrasing is fine).\n"
        "A sentence is 'ungrounded' if it adds major unsupported facts or contradicts the context.\n\n"
        "Score: proportion of grounded sentences (0.0 = none grounded, 1.0 = all grounded).\n"
        "Explanation: list which sentences lack evidence.\n\n"
        "Evaluate the response against the context provided in {{context}} and {{response}}."
    ),
    "RankingEvaluator": (
        "You are evaluating and ranking multiple contexts based on their relevance to a query.\n\n"
        "Given the user's input query in {{input}} and a list of contexts in {{context}}:\n"
        "1. Analyze each context for relevance to the query\n"
        "2. Consider factual accuracy, completeness, and direct relevance\n"
        "3. Assign a relevance score from 0.0 to 1.0\n"
        "4. Provide a ranking with explanations for each context's score\n\n"
        "Your explanation should detail why each context ranks where it does."
    ),
    "PerplexityEvaluator": (
        "You are evaluating the perplexity/quality of generated text.\n\n"
        "Analyze the text in {{input}} for:\n"
        "- Coherence and fluency\n"
        "- Grammatical correctness\n"
        "- Logical consistency\n"
        "- Natural language quality\n\n"
        "Score from 0.0 (incoherent/poor) to 1.0 (perfectly fluent and coherent)."
    ),
    "ChunkUtilization": (
        "You are evaluating how well the output utilizes the provided context chunks.\n\n"
        "Given:\n"
        "- Input query: {{input}}\n"
        "- Context chunks: {{context}}\n"
        "- Generated output: {{output}}\n\n"
        "Evaluate:\n"
        "1. What proportion of the context information is used in the output?\n"
        "2. Is relevant context ignored?\n"
        "3. Is irrelevant context appropriately excluded?\n\n"
        "Score from 0.0 (no context used) to 1.0 (all relevant context utilized)."
    ),
    "ChunkAttribution": (
        "You are evaluating whether the output properly attributes information to the provided context.\n\n"
        "Given:\n"
        "- Input: {{input}}\n"
        "- Context: {{context}}\n"
        "- Output: {{output}}\n\n"
        "Check if the output's claims can be traced back to the context.\n"
        "Pass if all major claims are attributable to context. Fail if claims are fabricated."
    ),
    "OutputEvaluator": (
        "You are evaluating the quality of an AI-generated output.\n\n"
        "Analyze {{output}} for:\n"
        "- Relevance to the task\n"
        "- Completeness of the response\n"
        "- Accuracy of information\n"
        "- Clarity and coherence\n\n"
        "Score from 0.0 (poor quality) to 1.0 (excellent quality)."
    ),
    "ConversationResolution": (
        "You are evaluating whether a conversation reaches a satisfactory resolution.\n\n"
        "Analyze the conversation in {{messages}} for:\n"
        "- Whether the user's original question/request was addressed\n"
        "- Whether the conversation ended with the user's needs met\n"
        "- Whether there are unresolved follow-ups\n\n"
        "Score from 0.0 (unresolved) to 1.0 (fully resolved)."
    ),
    "PiiDetection": (
        "You are evaluating text for Personally Identifiable Information (PII).\n\n"
        "Scan {{text}} for:\n"
        "- Names, email addresses, phone numbers\n"
        "- Social security numbers, credit card numbers\n"
        "- Physical addresses, IP addresses\n"
        "- Any other data that could identify a specific individual\n\n"
        "Pass if no PII found. Fail if PII is detected. List all PII found in explanation."
    ),
    "AudioTranscriptionEvaluator": (
        "You are evaluating the accuracy of an audio transcription.\n\n"
        "Compare the transcription in {{input transcription}} against the audio content from {{input audio}}.\n"
        "Evaluate:\n"
        "- Word accuracy\n"
        "- Preservation of meaning\n"
        "- Handling of speaker turns\n"
        "- Punctuation and formatting\n\n"
        "Score from 0.0 (completely inaccurate) to 1.0 (perfect transcription)."
    ),
    "ImageInstructionEvaluator": (
        "You are evaluating whether an image follows given instructions.\n\n"
        "Given the instructions in {{input}} and the image at {{image_url}}:\n"
        "1. Analyze the image content\n"
        "2. Check if it adheres to the instructions\n"
        "3. Note any deviations\n\n"
        "Score from 0.0 (completely wrong) to 1.0 (perfectly follows instructions)."
    ),
    "ContextSimilarity": (
        "You are evaluating the semantic similarity between a context and a response.\n\n"
        "Compare {{context}} and {{response}}:\n"
        "- Do they convey the same core information?\n"
        "- Are key facts preserved?\n"
        "- Is the meaning equivalent even if wording differs?\n\n"
        "Score from 0.0 (completely different) to 1.0 (semantically identical)."
    ),
    "LlmEvaluator": (
        "You are a general-purpose LLM evaluator.\n\n"
        "Evaluate the provided inputs according to the criteria given.\n"
        "Provide a clear score and detailed explanation."
    ),
    "BaseEvaluator": (
        "You are a general-purpose evaluator.\n\n"
        "Evaluate the provided inputs according to the criteria given.\n"
        "Provide a clear score and detailed explanation."
    ),
}


# ============================================================================
# Config transformers
# ============================================================================


def _to_agent_config(template):
    """DeterministicEvaluator/RankingEvaluator/system LLM evals → AgentEvaluator config."""
    old = copy.deepcopy(template.config or {})
    old_type = old.get("eval_type_id", "")
    new = {}

    new["eval_type_id"] = "AgentEvaluator"
    new["required_keys"] = old.get("required_keys", [])
    new["optional_keys"] = old.get("optional_keys", [])
    new["output"] = old.get("output", "Pass/Fail")

    # Rule prompt priority:
    # 1. Existing rule_prompt in config
    # 2. Template criteria field
    # 3. System eval prompt for this type
    # 4. Empty (should not happen)
    existing_prompt = (
        old.get("rule_prompt")
        or (old.get("config", {}) or {}).get("rule_prompt")
        or template.criteria
        or ""
    )
    # criteria can sometimes be a dict — coerce to string
    if not isinstance(existing_prompt, str):
        existing_prompt = str(existing_prompt) if existing_prompt else ""

    if existing_prompt.strip():
        new["rule_prompt"] = existing_prompt
    else:
        # Use system eval prompt for known types
        new["rule_prompt"] = SYSTEM_EVAL_PROMPTS.get(old_type, "")

    # Preserve the original type for reference
    new["original_eval_type_id"] = old_type

    # Agent fields
    new["agent_mode"] = old.get("agent_mode", "agent")
    new["tools"] = old.get("tools", {})
    new["knowledge_bases"] = old.get("knowledge_bases", [])
    new["check_internet"] = old.get("check_internet", False)
    new["data_injection"] = old.get("data_injection", {})
    new["summary"] = old.get("summary", {"type": "concise"})

    # Preserve extras
    for key in ("param_modalities", "config_params_desc", "model", "system_prompt"):
        if key in old:
            new[key] = old[key]

    return new, "agent"


def _to_code_config(template):
    """Function wrappers → CustomCodeEval config."""
    old = copy.deepcopy(template.config or {})
    old_type = old.get("eval_type_id", "")
    new = {}

    new["eval_type_id"] = "CustomCodeEval"
    new["required_keys"] = old.get("required_keys", [])
    new["optional_keys"] = old.get("optional_keys", [])
    new["output"] = old.get("output", "Pass/Fail")
    new["function_eval"] = True

    # Keep the original eval_type_id so we know what function to generate
    new["original_eval_type_id"] = old_type

    # Preserve the function config (keywords, pattern, schema, etc.)
    # This is stored in config.config for function evals
    inner_config = old.get("config", {})
    if isinstance(inner_config, dict):
        new["config"] = inner_config

    # Generate equivalent Python code
    new["code"] = _generate_code(old_type, inner_config, old)

    # Preserve extras
    for key in ("param_modalities", "config_params_desc"):
        if key in old:
            new[key] = old[key]

    return new, "code"


# ============================================================================
# Code generation for function wrappers
# ============================================================================

CODE_TEMPLATES = {
    "Contains": """def evaluate(output, **kwargs):
    keyword = {keyword!r}
    case_sensitive = {case_sensitive}
    if not case_sensitive:
        return keyword.lower() in str(output).lower()
    return keyword in str(output)
""",
    "ContainsAll": """def evaluate(output, **kwargs):
    keywords = {keywords!r}
    case_sensitive = {case_sensitive}
    text = str(output) if case_sensitive else str(output).lower()
    return all((k if case_sensitive else k.lower()) in text for k in keywords)
""",
    "ContainsAny": """def evaluate(output, **kwargs):
    keywords = {keywords!r}
    case_sensitive = {case_sensitive}
    text = str(output) if case_sensitive else str(output).lower()
    return any((k if case_sensitive else k.lower()) in text for k in keywords)
""",
    "ContainsNone": """def evaluate(output, **kwargs):
    keywords = {keywords!r}
    case_sensitive = {case_sensitive}
    text = str(output) if case_sensitive else str(output).lower()
    return not any((k if case_sensitive else k.lower()) in text for k in keywords)
""",
    "Regex": """import re
def evaluate(output, **kwargs):
    pattern = {pattern!r}
    return bool(re.search(pattern, str(output)))
""",
    "Equals": """def evaluate(output, expected_output, **kwargs):
    return str(output).strip() == str(expected_output).strip()
""",
    "StartsWith": """def evaluate(output, **kwargs):
    prefix = {prefix!r}
    return str(output).startswith(prefix)
""",
    "EndsWith": """def evaluate(output, **kwargs):
    suffix = {suffix!r}
    return str(output).endswith(suffix)
""",
    "LengthLessThan": """def evaluate(output, **kwargs):
    max_length = {max_length}
    return len(str(output)) < max_length
""",
    "LengthGreaterThan": """def evaluate(output, **kwargs):
    min_length = {min_length}
    return len(str(output)) > min_length
""",
    "LengthBetween": """def evaluate(output, **kwargs):
    min_length = {min_length}
    max_length = {max_length}
    length = len(str(output))
    return min_length <= length <= max_length
""",
    "OneLine": """def evaluate(output, **kwargs):
    return "\\n" not in str(output).strip()
""",
    "ContainsJson": """import json
def evaluate(output, **kwargs):
    try:
        json.loads(str(output))
        return True
    except (json.JSONDecodeError, TypeError):
        return False
""",
    "IsJson": """import json
def evaluate(output, **kwargs):
    try:
        json.loads(str(output))
        return True
    except (json.JSONDecodeError, TypeError):
        return False
""",
    "ContainsEmail": """import re
def evaluate(output, **kwargs):
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
    return bool(re.search(pattern, str(output)))
""",
    "IsEmail": """import re
def evaluate(output, **kwargs):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, str(output).strip()))
""",
    "ContainsLink": """import re
def evaluate(output, **kwargs):
    pattern = r"https?://[^\\s]+"
    return bool(re.search(pattern, str(output)))
""",
    "NoInvalidLinks": """import re
import urllib.request
def evaluate(output, **kwargs):
    urls = re.findall(r"https?://[^\\s]+", str(output))
    if not urls:
        return True
    for url in urls:
        try:
            urllib.request.urlopen(url, timeout=5)
        except Exception:
            return False
    return True
""",
    "ContainsValidLink": """import re
import urllib.request
def evaluate(output, **kwargs):
    urls = re.findall(r"https?://[^\\s]+", str(output))
    for url in urls:
        try:
            urllib.request.urlopen(url, timeout=5)
            return True
        except Exception:
            continue
    return False
""",
}

# Similarity/scoring evals — these need specialized libraries,
# keep the original class reference so they can be run via the original code
PASSTHROUGH_CODE = """# This eval uses the {eval_type} scoring function.
# Original eval_type_id preserved for backward compatibility.
# To customize, replace this with your own Python scoring logic.
def evaluate(**kwargs):
    raise NotImplementedError(
        "This eval ({eval_type}) requires migration to custom Python code. "
        "The original evaluator class is still used at runtime via original_eval_type_id."
    )
"""

SCORING_TYPES = {
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
    "JsonSchema",
    "JsonValidation",
    "ApiCall",
}


def _generate_code(eval_type_id, inner_config, full_config):
    """Generate Python code string for a function wrapper eval."""
    if not inner_config:
        inner_config = {}

    template = CODE_TEMPLATES.get(eval_type_id)
    if template:
        try:
            return template.format(**inner_config)
        except KeyError:
            # Config doesn't have expected keys — return with defaults
            return template

    if eval_type_id in SCORING_TYPES:
        return PASSTHROUGH_CODE.format(eval_type=eval_type_id)

    # Unknown function eval — generate placeholder
    return PASSTHROUGH_CODE.format(eval_type=eval_type_id)


# ============================================================================
# Main
# ============================================================================


def run(*args):
    dry_run = "--dry-run" in args

    from django.db import transaction

    from model_hub.models.evals_metric import EvalTemplate

    templates = EvalTemplate.no_workspace_objects.filter(deleted=False)
    total = templates.count()
    print(f"\nFound {total} eval templates to process")

    stats = {
        "to_agent": 0,
        "to_code": 0,
        "already_target": 0,
        "skipped_no_type": 0,
    }

    updates = []

    for tmpl in templates.iterator():
        config = tmpl.config or {}
        eval_type_id = config.get("eval_type_id", "")

        if not eval_type_id:
            stats["skipped_no_type"] += 1
            continue

        # Already one of the 3 target types — skip
        if eval_type_id in ALREADY_TARGET:
            stats["already_target"] += 1
            continue

        # Determine target
        if eval_type_id in TO_AGENT:
            new_config, new_eval_type = _to_agent_config(tmpl)
            stats["to_agent"] += 1
        elif eval_type_id in TO_AGENT_LLM:
            new_config, new_eval_type = _to_agent_config(tmpl)
            stats["to_agent"] += 1
        elif eval_type_id in TO_CODE:
            new_config, new_eval_type = _to_code_config(tmpl)
            stats["to_code"] += 1
        elif eval_type_id in TO_CODE_SIMILARITY:
            new_config, new_eval_type = _to_code_config(tmpl)
            stats["to_code"] += 1
        else:
            # Unknown type — default to agent (most capable)
            new_config, new_eval_type = _to_agent_config(tmpl)
            stats["to_agent"] += 1
            print(
                f"  WARN: Unknown eval_type_id '{eval_type_id}' on [{tmpl.id}] {tmpl.name} — defaulting to agent"
            )

        if dry_run:
            print(
                f"  [{tmpl.id}] {tmpl.name}: "
                f"{eval_type_id} -> {new_config['eval_type_id']} "
                f"(eval_type: {tmpl.eval_type} -> {new_eval_type})"
            )
        else:
            tmpl.config = new_config
            tmpl.eval_type = new_eval_type
            updates.append(tmpl)

    if not dry_run and updates:
        batch_size = 100
        with transaction.atomic():
            for i in range(0, len(updates), batch_size):
                batch = updates[i : i + batch_size]
                EvalTemplate.no_workspace_objects.bulk_update(
                    batch, ["config", "eval_type"], batch_size=batch_size
                )
        print(f"\nMigrated {len(updates)} templates")

    print(f"\n--- Stats ---")
    print(f"  Total templates:       {total}")
    print(f"  Already target type:   {stats['already_target']}")
    print(f"  Migrated to agent:     {stats['to_agent']}")
    print(f"  Migrated to code:      {stats['to_code']}")
    print(f"  Skipped (no type):     {stats['skipped_no_type']}")

    if dry_run:
        print(f"\n  *** DRY RUN — no changes written ***")
