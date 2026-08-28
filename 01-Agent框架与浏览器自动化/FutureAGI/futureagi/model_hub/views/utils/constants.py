import re

PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*(?P<placeholder>.*?)\s*\}\}")

EVAL_OUTPUT_TYPES = {
    "REASON": "reason",
    "CHOICES": "choices",
    "PASS_FAIL": "Pass/Fail",
    "SCORE": "score",
}
