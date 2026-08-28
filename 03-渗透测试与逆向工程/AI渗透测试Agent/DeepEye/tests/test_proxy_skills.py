"""proxy.system skill discovery — skills live under .agents/skills/."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def test_skills_dir_is_agents_skills():
    from proxy.system import skills_dir

    d = skills_dir()
    assert d.name == "skills"
    assert d.parent.name == ".agents"
    assert d.is_dir()


def test_list_skill_paths_nonempty():
    from proxy.system import list_skill_paths, list_skill_index

    paths = list_skill_paths()
    assert len(paths) >= 10
    idx = list_skill_index()
    assert any("vulnerabilities/sql_injection.md" in x for x in idx)
    assert any("pentest" in x for x in idx)


def test_available_skills_block_has_absolute_paths():
    from proxy.system import get_available_skills_block

    block = get_available_skills_block()
    assert "<available_skills>" in block
    assert "</available_skills>" in block
    assert "sql_injection.md" in block or "SKILL.md" in block
    # absolute path markers
    assert ":/" in block or "\\" in block or block.count("/") > 5


def test_find_and_read_skill():
    from proxy.system import find_skill, read_skill

    p = find_skill("sql_injection")
    assert p is not None
    assert p.is_file()
    body = read_skill("sql_injection")
    assert body and "SQL Injection" in body
    assert "Trigger condition" in body


def test_get_system_prompt():
    from proxy.system import get_system_prompt

    p = get_system_prompt()
    assert "authorized" in p.lower() or "Deep Eye" in p
    assert "<available_skills>" in p


def test_workflow_skills_present():
    from proxy.system import list_skill_index

    idx = " ".join(list_skill_index())
    for name in ("pentest", "bug-bounty", "red-team", "blue-team", "ctf", "security-ops"):
        assert name in idx
