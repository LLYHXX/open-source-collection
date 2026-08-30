import os, sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), 'vendor'))
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
try:
    from app.config import get_settings
    get_settings.cache_clear()
except Exception:
    pass
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.database as dbm
dbm.engine = create_engine('sqlite:///:memory:', echo=False, connect_args={'check_same_thread': False})
dbm.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dbm.engine)
from app.database import init_db
init_db()
print('[INFO] DB init OK')

from app.routers.miner import list_candidates, create_candidate
from app.models import Intel
import uuid as _uuid

db = dbm.SessionLocal()
try:
    # T1: status=new → pending alias
    r = list_candidates(status='new', page=1, page_size=50, keyword='', db=db)
    print(f'[T1] status=new       → success={r.success}, total={r.data["total"]}, msg={r.message[:60]}')
    assert r.success is True, 'status=new 必须 alias→pending'
    assert r.data['total'] == 0

    # T2: status=pending
    r = list_candidates(status='pending', page=1, page_size=50, keyword='', db=db)
    print(f'[T2] status=pending   → success={r.success}, total={r.data["total"]}')
    assert r.success is True

    # T3: 中文 待审核
    r = list_candidates(status='待审核', page=1, page_size=50, keyword='', db=db)
    print(f'[T3] status=待审核    → success={r.success}')
    assert r.success is True

    # T4: 非法 status → 不抛 HTTPException，返回 StandardResponse(success=False)
    r = list_candidates(status='INVALID_XXX', page=1, page_size=50, keyword='', db=db)
    print(f'[T4] status=INVALID   → success={r.success}, msg={r.message[:70]}')
    assert r.success is False
    assert r.data['total'] == 0

    # T5: keyword 搜索
    r = list_candidates(status='approved', page=1, page_size=20, keyword='test', db=db)
    print(f'[T5] status=approved+keyword → success={r.success}, total={r.data["total"]}')
    assert r.success is True

    # ---- 先插一条 Intel 作为外键锚点 ----
    src_intel = Intel(id=str(_uuid.uuid4()), kind='endpoint', key='example.com',
                      value='https://example.com', lifecycle='active',
                      confidence=0.9, source='smoke_test', tags=[])
    db.add(src_intel)
    db.commit()
    db.refresh(src_intel)
    print(f'[INFO] 预置 Intel id={src_intel.id[:8]}')

    # T6: POST /candidates → create (原 405 现在应 2xx)
    from app.routers.miner import MinerCandidateCreate
    payload = MinerCandidateCreate(
        src_intel_id=src_intel.id,
        extracted_kind='credential',
        extracted_key='admin:weakpass',
        status='pending',
        note='冒烟测试数据'
    )
    r = create_candidate(payload, db=db)
    print(f'[T6] POST candidates   → success={r.success}, msg={r.message[:50]}, id={r.data["id"][:8] if r.data else None}')
    assert r.success is True

    # T7: status=pending 现在应该 total=1，keyword=admin 能搜到
    r = list_candidates(status='pending', page=1, page_size=50, keyword='', db=db)
    print(f'[T7] pending count     → success={r.success}, total={r.data["total"]}')
    assert r.data['total'] == 1

    r = list_candidates(status='pending', page=1, page_size=50, keyword='admin', db=db)
    print(f'[T8] kw=admin hit      → success={r.success}, total={r.data["total"]}, items={len(r.data["items"])}')
    assert r.data['total'] == 1
    assert r.data['items'][0]['extracted_key'] == 'admin:weakpass'

    r = list_candidates(status='pending', page=1, page_size=50, keyword='NOT_EXIST', db=db)
    print(f'[T9] kw=NOT_EXIST miss → success={r.success}, total={r.data["total"]}')
    assert r.data['total'] == 0

    print()
    print('=== Miner API SMOKE: ALL 9/9 PASSED (接口 2xx 确认) ===')
finally:
    db.close()
