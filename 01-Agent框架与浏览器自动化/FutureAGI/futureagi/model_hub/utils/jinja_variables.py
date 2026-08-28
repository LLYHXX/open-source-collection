"""
Jinja2-aware variable extraction.

Uses jinja2.meta.find_undeclared_variables() to accurately identify which
variables are *external inputs* vs loop-scoped or set-scoped.
"""

from __future__ import annotations

import re

from jinja2 import Environment, TemplateSyntaxError, meta


def extract_jinja_variables(template: str | None) -> list[str]:
    """
    Extract top-level input variable names from a Jinja2 template.

    Correctly handles for-loops, set assignments, dotted access,
    filters, and conditionals via Jinja2's built-in AST analysis.

    Returns a sorted, deduplicated list of variable names.
    """
    if not template:
        return []

    env = Environment()
    try:
        ast = env.parse(template)
    except TemplateSyntaxError:
        return _fallback_extract(template)

    return sorted(meta.find_undeclared_variables(ast))


def _fallback_extract(template: str) -> list[str]:
    """Naive regex fallback for malformed templates: extract root names from {{ expr }}."""
    matches = re.findall(r"\{\{\s*([^{}]+?)\s*\}\}", template)
    roots: set[str] = set()
    for m in matches:
        name = m.strip().split("|")[0].strip()
        root = name.split(".")[0].strip()
        if root:
            roots.add(root)
    return sorted(roots)
