"""SQLAlchemy + SQLite 引擎与会话。"""
import logging
import os
from urllib.parse import urlparse

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import get_settings

log = logging.getLogger("aififteen-hunter")

settings = get_settings()


def _ensure_sqlite_dir(url: str) -> None:
    """sqlite 相对路径数据库：确保 data 目录存在，否则启动报 unable to open。"""
    if not url.startswith("sqlite"):
        return
    # 形如 sqlite:///./data/aififteen_hunter.db -> 取 ./data/aififteen_hunter.db
    path_part = url.replace("sqlite:///", "", 1)
    # 去掉查询参数
    path_part = path_part.split("?", 1)[0]
    if not path_part or path_part.startswith(":memory:"):
        return
    db_dir = os.path.dirname(os.path.abspath(path_part))
    os.makedirs(db_dir, exist_ok=True)


_ensure_sqlite_dir(settings.database_url)

# SQLite 并发稳定性：
# - timeout=30：驱动层 busy 等待（等价 busy_timeout 的一层兜底）
# - WAL 模式：读写不互斥（后台扫描长事务写库时，前端查询/写入不再立刻撞 locked）
# - busy_timeout=30s：拿不到写锁时等待而非立即 OperationalError
# - synchronous=NORMAL：WAL 下安全且更快
_is_sqlite = settings.database_url.startswith("sqlite")
_is_memory_sqlite = ":memory:" in settings.database_url
connect_args = (
    {"check_same_thread": False, "timeout": 30}
    if _is_sqlite
    else {}
)
engine = create_engine(settings.database_url, connect_args=connect_args, echo=False)


if _is_sqlite:
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _rec):
        """每个新连接落地 PRAGMA：WAL + busy_timeout + 外键。"""
        cur = dbapi_conn.cursor()
        try:
            # 内存库不支持 WAL（WAL 需要文件共享内存），跳过
            if not _is_memory_sqlite:
                cur.execute("PRAGMA journal_mode=WAL")
                cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA busy_timeout=30000")
            cur.execute("PRAGMA foreign_keys=ON")
        finally:
            cur.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _sqlite_add_column_with_retry(tname: str, col, type_str: str, default_clause: str, nullable_clause: str) -> None:
    """单条 ADD COLUMN：SQLite 3.35+ NOT NULL+DEFAULT 优先级→降级→重试锁。
    单条失败最终会 raise RuntimeError，避免"静默忽略"→后续所有操作炸 500。"""
    import time as _time
    # 按约束从强到弱尝试：(NOT NULL+DEFAULT, NOT NULL 仅当无 DEFAULT, DEFAULT 仅当可空, 完全裸)
    attempts: list[tuple[str, str]] = []
    if nullable_clause and default_clause:
        attempts.append(("strong", f'ALTER TABLE "{tname}" ADD COLUMN "{col.name}" {type_str}{default_clause}{nullable_clause}'))
    if nullable_clause:
        attempts.append(("not-null", f'ALTER TABLE "{tname}" ADD COLUMN "{col.name}" {type_str}{nullable_clause}'))
    if default_clause:
        attempts.append(("default", f'ALTER TABLE "{tname}" ADD COLUMN "{col.name}" {type_str}{default_clause}'))
    attempts.append(("bare", f'ALTER TABLE "{tname}" ADD COLUMN "{col.name}" {type_str}'))

    from sqlalchemy.dialects import sqlite as _sqlite_dialect  # noqa: F401
    last_exc: Exception | None = None
    for label, stmt in attempts:
        # 每条尝试都做 3 次锁重试（database is locked 是用户高频问题：GUI 启动器双开、debug 多进程）
        for retry in range(3):
            try:
                with engine.begin() as conn:
                    conn.execute(text(stmt))
                log.info("[migrate] 表 %s 新增列 %s 方式=%s  OK", tname, col.name, label)
                return
            except Exception as e:  # noqa: BLE001
                last_exc = e
                low = str(e).lower()
                is_lock = "locked" in low
                is_constraint = "constraint" in low or "not null" in low or "default" in low
                # 重复列=列已存在（多进程双开竞态/重复迁移）：幂等视为成功
                if "duplicate" in low:
                    log.info("[migrate] 表 %s 列 %s 已存在（跳过）", tname, col.name)
                    return
                if not is_lock and not is_constraint:
                    log.warning("[migrate] 表 %s 列 %s 方式=%s 非预期异常: %s", tname, col.name, label, e)
                if is_lock and retry < 2:
                    wait = (retry + 1) * 0.5
                    log.warning("[migrate] 表 %s 列 %s 数据库被锁，%.1fs 后重试 (retry=%d/2): %s",
                                tname, col.name, wait, retry + 1, e)
                    _time.sleep(wait)
                    continue
                break  # 下一种尝试方式
    # 全部失败（含裸语句仍然锁/不支持）
    raise RuntimeError(
        f"[migrate] 致命：无法为表 {tname} 新增列 {col.name}（SQLite ADD COLUMN 全部降级方式均失败）。"
        f" 请关闭所有正在访问本数据库的进程后重试。最近错误: {type(last_exc).__name__}: {last_exc}"
    )


def _sqlite_alter_add_missing_columns() -> None:
    """SQLite 兼容迁移：create_all 后对每张已存在表对比模型列，缺就 ALTER TABLE ADD。

    SQLite 只支持 ADD COLUMN 一种 ALTER；不改列类型、不移除列，
    保证旧数据 0 破坏。幂等，可重复调用。失败则 fail-fast，绝不"静默忽略"。
    """
    if not settings.database_url.startswith("sqlite"):
        return
    insp = inspect(engine)
    # 避免在 init_db 之前还没 import models；这里延迟引用
    from sqlalchemy.orm import class_mapper

    for cls in Base.__subclasses__():
        try:
            mapper = class_mapper(cls)
        except Exception:  # noqa: BLE001 非映射类（如 Mixin）忽略
            continue
        table = mapper.local_table
        if table is None:
            continue
        tname = table.name
        if not insp.has_table(tname):
            continue  # create_all 会新建，不用 alter
        existing_cols = {c["name"] for c in insp.get_columns(tname)}
        for col in table.columns:
            if col.name in existing_cols:
                continue
            # SQLite 不支持 primary key / unique 约束加在 ADD COLUMN 上（除了 integer pk）
            # 所以若列是 pk 或复杂约束跳过（create_all 会创建整张表，不会来到这个分支）
            if col.primary_key:
                continue
            # 构造类型字符串：取 col.type.compile(dialect=sqlite)
            from sqlalchemy.dialects import sqlite as _sqlite_dialect
            type_str = col.type.compile(dialect=_sqlite_dialect.dialect())
            default_clause = ""
            if col.default is not None and col.default.is_scalar:
                raw = col.default.arg
                if isinstance(raw, bool):
                    default_clause = f" DEFAULT {'1' if raw else '0'}"
                elif isinstance(raw, (int, float)):
                    default_clause = f" DEFAULT {raw}"
                elif raw is None:
                    default_clause = " DEFAULT NULL"
                else:
                    esc = str(raw).replace("'", "''")
                    default_clause = f" DEFAULT '{esc}'"
            nullable_clause = "" if col.nullable else " NOT NULL"
            # SQLite 3.35+ 才支持 DEFAULT with NOT NULL on ADD COLUMN
            _sqlite_add_column_with_retry(tname, col, type_str, default_clause, nullable_clause)


def init_db():
    # 确保所有 ORM 模型已注册到 Base.metadata（否则 create_all + alter 看不到）
    from . import models  # noqa: F401  触发模型类加载
    Base.metadata.create_all(bind=engine, checkfirst=True)
    _sqlite_alter_add_missing_columns()
