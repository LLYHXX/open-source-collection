"""技能包系统：纯提示词+配方打包（绝不执行包内代码）。

包结构：
  skillpack.json   # {name, version, description, author, prompts: {角色: 文件}, recipes: [...]}
  prompts/*.md     # 按角色的提示词片段
  recipes/*.json   # 扫描配方（展示用，二期接一键建任务）

安装来源：GitHub 仓库（git clone --depth 1，走系统 git 配置的代理）或本地目录。
安装目录：backend/data/skillpacks/<name>（沙箱目录，仅读提示词文本）。
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path


def _data_dir() -> Path:
    """与 database.py 同款约定：数据目录取自 sqlite url 的父目录。"""
    try:
        from ..config import get_settings
        url = get_settings().database_url
        if url.startswith("sqlite:///") and ":memory:" not in url:
            return Path(url.replace("sqlite:///", "", 1)).parent
    except Exception:  # noqa: BLE001
        pass
    return Path("data")


SKILLPACKS_DIR = _data_dir() / "skillpacks"
_NAME_RE = re.compile(r"^[A-Za-z0-9_\-\u4e00-\u9fff]{1,64}$")
_MAX_PROMPT_CHARS = 8000  # 单包提示词拼接上限（防 token 爆炸）


class SkillPackError(Exception):
    """技能包安装/校验错误。"""


def _validate_pack_dir(pack_dir: Path) -> dict:
    """校验目录为合法技能包，返回 manifest。"""
    manifest_path = pack_dir / "skillpack.json"
    if not manifest_path.is_file():
        raise SkillPackError("缺少 skillpack.json（技能包清单）")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        raise SkillPackError(f"skillpack.json 解析失败: {e}") from e
    if not isinstance(manifest, dict):
        raise SkillPackError("skillpack.json 必须是 JSON 对象")
    name = str(manifest.get("name", "")).strip()
    if not _NAME_RE.match(name):
        raise SkillPackError(f"manifest.name 非法: {name!r}（限中英文/数字/-/_，≤64字符）")
    if not manifest.get("version"):
        manifest["version"] = "1.0.0"
    prompts = manifest.get("prompts")
    if not isinstance(prompts, dict) or not prompts:
        raise SkillPackError("manifest.prompts 必须是非空对象 {角色: 提示词文件}")
    # 校验 prompts 引用的文件存在且为 .md 文本
    for role, fname in prompts.items():
        p = pack_dir / str(fname)
        if not p.is_file() or p.suffix.lower() not in (".md", ".txt"):
            raise SkillPackError(f"提示词文件缺失或非文本: {role} -> {fname}")
    return manifest


def _copy_pack(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst,
                    ignore=shutil.ignore_patterns(".git*", "__pycache__", "*.py"))


def install_from_local(local_path: str) -> tuple[dict, Path]:
    """从本地目录安装（校验后拷贝进 data/skillpacks/）。"""
    src = Path(local_path).resolve()
    if not src.is_dir():
        raise SkillPackError(f"本地目录不存在: {local_path}")
    manifest = _validate_pack_dir(src)
    dst = SKILLPACKS_DIR / manifest["name"]
    _copy_pack(src, dst)
    return manifest, dst


def install_from_git(git_url: str) -> tuple[dict, Path]:
    """从 GitHub 仓库安装：浅克隆到临时目录→校验→拷贝。

    仅读取包内文本文件，不执行任何包内代码（git 本身除外）。
    """
    git_url = (git_url or "").strip()
    if not git_url.startswith(("https://", "http://", "git@")):
        raise SkillPackError("git_url 必须是 http(s) 或 git@ 开头的仓库地址")
    import tempfile

    with tempfile.TemporaryDirectory(prefix="skillpack_") as tmp:
        tmp = Path(tmp)
        clone_dir = tmp / "repo"
        try:
            proc = subprocess.run(
                ["git", "clone", "--depth", "1", git_url, str(clone_dir)],
                capture_output=True, text=True, timeout=300,
            )
        except subprocess.TimeoutExpired as e:
            raise SkillPackError("git clone 超时(300s)") from e
        if proc.returncode != 0:
            raise SkillPackError(f"git clone 失败: {(proc.stderr or proc.stdout).strip()[:500]}")
        # 允许 manifest 在仓库根或任一一级子目录
        if (clone_dir / "skillpack.json").is_file():
            return install_from_local(str(clone_dir))
        for child in clone_dir.iterdir():
            if child.is_dir() and (child / "skillpack.json").is_file():
                return install_from_local(str(child))
        raise SkillPackError("仓库根目录及一级子目录均未找到 skillpack.json")


def prompt_suffix(db, roles: tuple[str, ...] = ()) -> str:
    """汇总所有启用技能包的提示词，拼接为 Agent system prompt 附加段。

    roles 为空 = 取全部角色（Worker 用法）。单包截断防 token 爆炸。
    """
    from ..models import SkillPack

    parts: list[str] = []
    packs = db.query(SkillPack).filter(SkillPack.enabled.is_(True)).all()
    for pack in packs:
        try:
            manifest = json.loads(pack.manifest or "{}")
        except Exception:  # noqa: BLE001
            continue
        prompts = manifest.get("prompts") or {}
        pack_dir = Path(pack.path) if pack.path else None
        if not pack_dir or not pack_dir.is_dir():
            continue
        texts: list[str] = []
        for role, fname in prompts.items():
            if roles and role not in roles:
                continue
            p = pack_dir / str(fname)
            if p.is_file() and p.suffix.lower() in (".md", ".txt"):
                try:
                    texts.append(p.read_text(encoding="utf-8", errors="replace").strip())
                except Exception:  # noqa: BLE001
                    continue
        if not texts:
            continue
        body = "\n\n".join(texts)
        if len(body) > _MAX_PROMPT_CHARS:
            body = body[:_MAX_PROMPT_CHARS] + "\n…（技能包提示词过长已截断）"
        parts.append(f"### 技能包: {pack.name} v{pack.version}\n{body}")
    if not parts:
        return ""
    return "\n\n以下是已启用技能包的战术指令（对本次任务生效）：\n\n" + "\n\n".join(parts)
