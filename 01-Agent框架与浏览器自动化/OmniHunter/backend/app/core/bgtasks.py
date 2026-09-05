"""后台任务安全包装：所有 fire-and-forget 协程必须走 safe_create_task。

解决两类稳定性问题：
1. asyncio.create_task 的游离任务抛异常后 "Task exception was never retrieved"，
   在 uvicorn/anyio 栈里可能冒泡成 ExceptionGroup 打断请求任务；
2. 后台任务异常静默，用户只看到"后端突然没反应"，无日志可查。

本模块统一：全量捕获 → 记录 request 无关的后台错误日志 → 可选回调修正持久化状态。
"""
from __future__ import annotations

import asyncio
import functools
import logging
import traceback
from typing import Any, Awaitable, Callable

log = logging.getLogger("aififteen-hunter")


def safe_create_task(coro: Awaitable[Any], *,
                     name: str = "",
                     on_error: Callable[[BaseException], None] | None = None
                     ) -> asyncio.Task:
    """包装协程为后台任务：异常全捕获 + 落日志，绝不逃逸到事件循环。

    用法：
        safe_create_task(Orchestrator(db).run_task(tid), name=f"task:{tid}")

    on_error: 可选同步回调，接收异常对象，用于修正持久化状态
              （如把卡住的 Task 标记 failed）。回调自身异常会被吞掉并记录。
    """
    async def _runner() -> None:
        label = name or getattr(coro, "__qualname__", "background")
        try:
            await coro
        except asyncio.CancelledError:
            # 关闭时正常取消，不算错误
            raise
        except BaseException as e:  # noqa: BLE001 后台任务必须兜住一切
            log.error("[bg-task:%s] 未捕获异常: %s\n%s",
                      label, e, traceback.format_exc())
            if on_error is not None:
                try:
                    on_error(e)
                except Exception as cb_e:  # noqa: BLE001
                    log.error("[bg-task:%s] on_error 回调失败: %s", label, cb_e)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # 无运行循环（极端场景/同步上下文）：直接关闭协程避免警告
        log.warning("safe_create_task 无运行中的事件循环，任务 %s 未执行", name)
        coro.close() if hasattr(coro, "close") else None
        raise

    task = loop.create_task(_runner(), name=name or "aif-bg")
    # 双保险：task 自身 done callback 再捞一次异常（防止 _runner 未来被改坏）
    def _on_done(t: asyncio.Task) -> None:
        if t.cancelled():
            return
        exc = t.exception()
        if exc is not None:
            log.error("[bg-task:%s] done-callback 捕获残余异常: %s",
                      name or "aif-bg", exc)
    task.add_done_callback(_on_done)
    return task


def install_loop_exception_handler() -> None:
    """在主事件循环上安装兜底异常处理器。

    捕获所有"无人 retrieve"的游离任务异常，只记录不抛出，
    防止 uvicorn 进程因未处理回调异常退出。lifespan 启动时调用一次。
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    def _handler(_loop: asyncio.AbstractEventLoop, context: dict) -> None:
        exc = context.get("exception")
        msg = context.get("message", "(no message)")
        if isinstance(exc, asyncio.CancelledError):
            return
        log.error(
            "[event-loop] 未处理异常: %s | task=%s | %s",
            msg,
            context.get("task"),
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            if exc else "",
        )

    loop.set_exception_handler(_handler)
    log.info("事件循环兜底异常处理器已安装")


def mark_task_failed_on_error(task_id: str) -> Callable[[BaseException], None]:
    """生成 on_error 回调：后台流水线炸了时把 Task 状态修正为 failed。

    硬约束：后台异步任务异常必须同步修正已持久化的中间状态，防止状态不一致。
    """
    def _cb(exc: BaseException) -> None:
        # 延迟 import 避免循环依赖
        from ..database import SessionLocal
        from ..models import Task
        db = SessionLocal()
        try:
            t = db.get(Task, task_id)
            if t and t.status in ("collecting", "running", "pending"):
                t.status = "failed"
                t.error = f"[{type(exc).__name__}] {str(exc)[:1800]}"
                db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
        finally:
            db.close()
    return _cb


def safe_background(func: Callable[..., Awaitable[Any]]):
    """装饰器：让 async 路由里的后台协程函数自带安全包装语义（文档化用途）。

    实际调度仍建议显式 safe_create_task(func(...))。
    """
    @functools.wraps(func)
    async def _wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except asyncio.CancelledError:
            raise
        except BaseException as e:  # noqa: BLE001
            log.error("[bg-func:%s] 异常: %s\n%s",
                      getattr(func, "__name__", "?"), e, traceback.format_exc())
            raise
    return _wrapper
