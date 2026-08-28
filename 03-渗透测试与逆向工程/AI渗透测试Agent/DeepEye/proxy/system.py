"""Skill discovery for Deep Eye agents.

Scans ``.agents/skills/**/*.md`` (and legacy ``proxy/skills/`` if present)
and injects absolute paths into an ``<available_skills>`` block for on-demand
``read_file`` loading.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
_AGENTS_SKILLS = _REPO_ROOT / ".agents" / "skills"
_LEGACY_PROXY_SKILLS = Path(__file__).resolve().parent / "skills"

_METHODOLOGY = (
    "You are a security testing agent using Deep Eye.\n\n"
    "Rules:\n"
    "- Only test authorized targets.\n"
    "- Prefer Deep Eye CLI/modules before inventing one-off scripts.\n"
    "- Load skill documents on demand via absolute paths in <available_skills>.\n"
    "- Skills hold deep technique knowledge; do not preload all of them.\n"
    "- Report findings with type, severity, url, parameter, payload, evidence, remediation.\n"
)


def skills_dir() -> Path:
    if _AGENTS_SKILLS.is_dir():
        return _AGENTS_SKILLS
    return _LEGACY_PROXY_SKILLS


def _skill_roots() -> List[Path]:
    roots = []
    if _AGENTS_SKILLS.is_dir():
        roots.append(_AGENTS_SKILLS)
    if (
        _LEGACY_PROXY_SKILLS.is_dir()
        and _LEGACY_PROXY_SKILLS.resolve() != _AGENTS_SKILLS.resolve()
    ):
        roots.append(_LEGACY_PROXY_SKILLS)
    return roots


def list_skill_paths() -> List[Path]:
    paths: List[Path] = []
    seen = set()
    for root in _skill_roots():
        for p in sorted(root.rglob("*.md")):
            if not p.is_file():
                continue
            key = p.resolve()
            if key in seen:
                continue
            seen.add(key)
            paths.append(p)
    return sorted(paths, key=lambda x: x.as_posix().lower())


def list_skill_index() -> List[str]:
    primary = skills_dir()
    out = []
    for p in list_skill_paths():
        try:
            out.append(p.relative_to(primary).as_posix())
        except ValueError:
            try:
                out.append(p.relative_to(_REPO_ROOT).as_posix())
            except ValueError:
                out.append(p.as_posix())
    return out


def _load_local_skills() -> str:
    parts = [
        "You have access to the following skill documents. If you need specific guidance",
        "on a topic, use the `read_file` tool with the EXACT absolute path listed below:",
    ]
    paths = list_skill_paths()
    if not paths:
        parts.append("- (no skills found under .agents/skills/)")
    else:
        for path in paths:
            parts.append(f"- {path.absolute().as_posix()}")
    return "\n".join(parts)


def get_available_skills_block() -> str:
    return f"<available_skills>\n{_load_local_skills()}\n</available_skills>"


def get_system_prompt(extra: Optional[str] = None) -> str:
    blocks = [_METHODOLOGY.strip(), get_available_skills_block()]
    if extra:
        blocks.append(extra.strip())
    return "\n\n".join(blocks)


def find_skill(name_substring: str) -> Optional[Path]:
    key = (name_substring or "").lower().replace("\\", "/")
    if not key:
        return None
    for p in list_skill_paths():
        rel = p.as_posix().lower()
        if key in rel or key in p.stem.lower():
            return p
    return None


def read_skill(name_substring: str) -> Optional[str]:
    path = find_skill(name_substring)
    if not path:
        return None
    return path.read_text(encoding="utf-8")
