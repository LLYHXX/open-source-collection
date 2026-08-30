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

connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)
engine = create_engine(settings.database_url, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _sqlite_alter_add_missing_columns() -> None:
    """SQLite 兼容迁移：create_all 后对每张已存在表对比模型列，缺就 ALTER TABLE ADD。

    SQLite 只支持 ADD COLUMN 一种 ALTER；不改列类型、不移除列，
    保证旧数据 0 破坏。幂等，可重复调用。
    """
    if not settings.database_url.startswith("sqlite"):
        return
    insp = inspect(engine)
    # 避免在 init_db 之前还没 import models；这里延迟引用
    from sqlalchemy.orm import class_mapper

    with engine.begin() as conn:
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
                # SQLite 3.35+ 才支持 DEFAULT with NOT NULL on ADD COLUMN；
                # 若有 NOT NULL + default，兼容模式下先不加 NOT NULL。
                if nullable_clause and default_clause:
                    stmt = f'ALTER TABLE "{tname}" ADD COLUMN "{col.name}" {type_str}{default_clause}{nullable_clause}'
                    try:
                        conn.execute(text(stmt))
                        log.info("迁移：表 %s 新增列 %s（含默认值+NOT NULL）", tname, col.name)
                        continue
                    except Exception as _e:  # noqa: BLE001
                        log.warning("兼容降级表 %s 列 %s：%s", tname, col.name, _e)
                stmt = f'ALTER TABLE "{tname}" ADD COLUMN "{col.name}" {type_str}{default_clause}'
                try:
                    conn.execute(text(stmt))
                    log.info("迁移：表 %s 新增列 %s", tname, col.name)
                except Exception as e:  # noqa: BLE001
                    log.warning("迁移表 %s 列 %s 失败（忽略）: %s", tname, col.name, e)


def init_db():
    # 确保所有 ORM 模型已注册到 Base.metadata（否则 create_all + alter 看不到）
    from . import models  # noqa: F401  触发模型类加载
    Base.metadata.create_all(bind=engine, checkfirst=True)
    _sqlite_alter_add_missing_columns()
