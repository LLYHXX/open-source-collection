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

from ..models import SkillPack


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


_BASH_EXE: str | None = None


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
    if not (src / "skillpack.json").is_file():
        # 无清单：自动转换（兼容 Claude skills 的 SKILL.md 与任意 markdown 目录）
        return _install_repo_as_pack(src, src.name)
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
                # 绕过全局代理直连（代理客户端未开时 clone GitHub 必失败）
                ["git", "-c", "http.proxy=", "-c", "https.proxy=",
                 "clone", "--depth", "1", git_url, str(clone_dir)],
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
        # 自动适配主流格式：无 skillpack.json 时把仓库整体转为技能包
        # （兼容 Claude skills 的 SKILL.md 约定与任意 markdown 提示词仓库）
        return _install_repo_as_pack(clone_dir, git_url)


def _install_repo_as_pack(repo_dir: Path, git_url: str) -> tuple[dict, Path]:
    """把无清单仓库自动转成技能包：收集 markdown 提示词生成 skillpack.json。

    兼容来源：Claude skills 仓库（SKILL.md frontmatter）、任意 *.md 知识仓库。
    收集上限 16 个文件、总量 200KB，防止巨型仓库拖垮提示词注入。
    """
    repo_name = git_url.rstrip("/").split("/")[-1]
    repo_name = re.sub(r"\.git$", "", repo_name) or "skillpack"
    name = re.sub(r"[^A-Za-z0-9_\-\u4e00-\u9fff]", "-", repo_name)[:64].strip("-") or "skillpack"

    skip_parts = {".git", "node_modules", "__pycache__", "dist", "build"}
    md_files: list[Path] = []
    for p in sorted(repo_dir.rglob("*.md")):
        if skip_parts & set(p.parts):
            continue
        md_files.append(p)
        if len(md_files) >= 16:
            break
    # SKILL.md 优先排序
    md_files.sort(key=lambda p: (0 if p.name.upper() == "SKILL.MD" else 1, str(p)))
    total = 0
    keep: list[Path] = []
    for p in md_files:
        try:
            sz = p.stat().st_size
        except OSError:
            continue
        if total + sz > 200 * 1024:
            continue
        total += sz
        keep.append(p)
    if not keep:
        raise SkillPackError("仓库内未找到任何 .md 技能/提示词文件，无法自动转换")

    # 描述：优先 README 首个非标题段，其次首个 SKILL.md 的 frontmatter description
    desc = f"自动转换自 {repo_name}"
    for cand in (repo_dir / "README.md", *(p for p in keep if p.name.upper() == "SKILL.MD")):
        try:
            text = cand.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        m = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
        if m and cand.name.upper() == "SKILL.MD":
            desc = m.group(1).strip()[:200]
            break
        for line in text.splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                desc = s[:200]
                break
        if desc != f"自动转换自 {repo_name}":
            break

    manifest = {
        "name": name,
        "version": "1.0.0",
        "description": desc,
        "author": "auto-converted",
        "prompts": {"worker": [str(p.relative_to(repo_dir)).replace("\\", "/") for p in keep]},
    }
    dst = SKILLPACKS_DIR / name
    _copy_pack(repo_dir, dst)
    (dst / "skillpack.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest, dst


def _find_bash() -> str:
    """定位真正的 Git Bash（排除 WSL bash——它不认 Windows 路径）。结果缓存。"""
    global _BASH_EXE
    if _BASH_EXE is not None:
        return _BASH_EXE
    for cand in (r"C:\Program Files\Git\bin\bash.exe",
                 r"C:\Program Files\Git\usr\bin\bash.exe",
                 r"C:\Program Files (x86)\Git\bin\bash.exe"):
        if Path(cand).is_file():
            _BASH_EXE = cand
            return _BASH_EXE
    w = shutil.which("bash") or ""
    _BASH_EXE = "" if "system32" in w.lower() else w
    return _BASH_EXE


def register_pack_tools(reg, db) -> int:
    """技能包 v2：把启用包内 scripts/ 目录的可执行脚本注册为 ToolRegistry 工具。

    发现规则：包目录下任意 scripts/ 子目录内的 .py/.sh/.ps1（兼容 Claude skills
    的 skills/<name>/scripts/ 约定）。工具名 pack_<包名>_<脚本名>，调用时 args.args
    作为命令行参数透传，cwd=脚本所在目录（相对资源可直达），超时 120s，输出截断 20KB。
    返回注册的工具数。仅执行包目录内文件。
    """
    packs = db.query(SkillPack).filter(SkillPack.enabled.is_(True)).all()
    count = 0
    for p in packs:
        pack_dir = Path(p.path)
        if not pack_dir.is_dir():
            continue
        for script in sorted(pack_dir.rglob("*")):
            if (script.suffix.lower() not in (".py", ".sh", ".ps1")
                    or script.parent.name != "scripts"):
                continue
            stem = re.sub(r"[^A-Za-z0-9_]", "_", script.stem)[:32].strip("_") or "tool"
            tool_name = f"pack_{re.sub(r'[^A-Za-z0-9_]', '_', p.name)[:24]}_{stem}"
            if reg.has(tool_name):
                continue

            def _run(script_path=script, pack_root=pack_dir, **kwargs):
                extra = str(kwargs.get("args") or "").strip()
                # 绝对路径：规避 Git Bash 相对 cwd 与反斜杠转义问题
                sp = str(script_path.resolve()).replace("\\", "/")
                root = str(pack_root.resolve())
                if sp.lower().endswith(".py"):
                    import sys
                    cmd = [sys.executable, sp]
                elif sp.lower().endswith(".ps1"):
                    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                           "-File", sp]
                else:
                    bash = _find_bash()
                    if not bash:
                        return "[缺运行时] 未找到 Git Bash，.sh 脚本无法执行（请安装 Git for Windows）"
                    cmd = [bash, sp]
                if extra:
                    cmd.extend(extra.split())
                try:
                    proc = subprocess.run(
                        cmd, cwd=root, capture_output=True, text=True,
                        timeout=120, errors="replace",
                    )
                except subprocess.TimeoutExpired:
                    return f"[超时] {tool_name} 执行超过 120s"
                except FileNotFoundError as e:
                    return f"[缺运行时] {e}"
                out = ((proc.stdout or "") + (proc.stderr or "")).strip()
                return f"[exit={proc.returncode}]\n{out[:20000]}"

            reg.register(
                tool_name, _run,
                description=f"技能包[{p.name}]脚本 {script.relative_to(pack_dir)}",
                parameters={
                    "type": "object",
                    "properties": {
                        "args": {"type": "string",
                                 "description": "传给脚本的命令行参数（空格分隔）"},
                    },
                },
            )
            count += 1
    return count


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
