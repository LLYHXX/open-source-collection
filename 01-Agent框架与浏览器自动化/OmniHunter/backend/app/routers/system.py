"""系统路由：一键更新 + 版本信息。

一键更新 = git pull（增量拉取，不重新下载整包）+ pip install 同步依赖。
配合 uvicorn --reload 即可热更新，无需重新下载/重新部署。
"""
import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends

from ..auth import verify_token
from ..schemas import StandardResponse

router = APIRouter(prefix="/system", tags=["system"],
                   dependencies=[Depends(verify_token)])

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
_REPO_HINTS = ["https://pypi.tuna.tsinghua.edu.cn/simple"]


def _git_root() -> str:
    """从 backend 目录向上找 git 仓库根。"""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(_BACKEND_DIR), capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or str(_BACKEND_DIR)
    except Exception:  # noqa: BLE001 非 git 仓库或无 git
        return str(_BACKEND_DIR)


@router.get("/version", response_model=StandardResponse)
def version():
    commit = ""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_git_root(), capture_output=True, text=True, timeout=10,
        )
        commit = out.stdout.strip()
    except Exception:  # noqa: BLE001
        pass
    return StandardResponse(data={
        "version": "0.1.0",
        "commit": commit,
        "repo_root": _git_root(),
    })


@router.post("/update", response_model=StandardResponse)
def update():
    """一键更新：git pull 增量拉取代码 + pip install 同步依赖。

    不重新下载整包，只拉变更。配合 uvicorn --reload 后端自动热重载。
    """
    root = _git_root()
    logs = []

    # 1) git pull 增量更新（不重新下载）
    try:
        out = subprocess.run(
            ["git", "-C", root, "pull", "--ff-only"],
            capture_output=True, text=True, timeout=120,
        )
        logs.append(f"[git pull]\n{(out.stdout or '') + (out.stderr or '')}".strip())
    except subprocess.TimeoutExpired:
        logs.append("[git pull] 超时(120s)")
    except Exception as e:  # noqa: BLE001
        logs.append(f"[git pull] 失败: {e}\n（若未用 git 管理可忽略，手动替换文件）")

    # 2) pip install 同步依赖（装到 vendor，避免污染系统）
    req = _BACKEND_DIR / "requirements.txt"
    if req.exists():
        try:
            out = subprocess.run(
                ["python", "-m", "pip", "install", "-r", str(req),
                 "--target", str(_BACKEND_DIR / "vendor"),
                 "-i", _REPO_HINTS[0]],
                cwd=str(_BACKEND_DIR),
                capture_output=True, text=True, timeout=300,
            )
            tail = (out.stdout or "")[-1500:] + (out.stderr or "")[-800:]
            logs.append(f"[pip install]\n{tail}".strip())
        except subprocess.TimeoutExpired:
            logs.append("[pip install] 超时(300s)")
        except Exception as e:  # noqa: BLE001
            logs.append(f"[pip install] 失败: {e}")

    msg = "更新完成。后端用 --reload 启动会自动热重载；前端 dev 模式热重载，"
    msg += "生产构建需重新 npm run build。"
    return StandardResponse(message=msg, data={"logs": "\n\n".join(logs)})
