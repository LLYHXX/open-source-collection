"""SQLAlchemy + SQLite 引擎与会话。"""
import os
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import get_settings

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


def init_db():
    Base.metadata.create_all(bind=engine)
