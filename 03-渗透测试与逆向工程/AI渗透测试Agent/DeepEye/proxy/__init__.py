"""proxy package — agent skill loading."""
from proxy.system import (
    find_skill,
    get_available_skills_block,
    get_system_prompt,
    list_skill_index,
    list_skill_paths,
    read_skill,
    skills_dir,
)

__all__ = [
    "find_skill",
    "get_available_skills_block",
    "get_system_prompt",
    "list_skill_index",
    "list_skill_paths",
    "read_skill",
    "skills_dir",
]
