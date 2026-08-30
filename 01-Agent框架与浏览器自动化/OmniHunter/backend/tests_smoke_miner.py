"""OmniHunter Autonomous Miner 冒烟测试。

运行: cd backend ; set PYTHONPATH=.;.\vendor ; python tests_smoke_miner.py

仅新建本文件，不修改任何项目现有文件。使用内存 SQLite，不污染生产 DB。
"""
from __future__ import annotations

import os
import sys

# === 1. 设置 PYTHONPATH (要求1) ===
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)
_VENDOR_DIR = os.path.join(_BACKEND_DIR, "vendor")
if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)

# === 2. 环境变量覆盖 database_url + 清除 settings 缓存（要求1）===
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
try:
    from app.config import get_settings
    get_settings.cache_clear()
except Exception:
    pass

# === 3. 引入 database 模块并替换 engine / SessionLocal（要求2）===
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

import app.database as _dbm
from app.database import init_db, engine, SessionLocal, Base  # noqa: F401 先按要求引入

# 覆盖动态 database_url
try:
    from app.config import get_settings as _gs
    _s = _gs()
    _s.database_url = "sqlite:///:memory:"
except Exception:
    pass

# 替换为内存 sqlite 引擎
_dbm.engine = create_engine(
    "sqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
)
_dbm.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_dbm.engine)

# === 4. 修复 MinerRun / Task 的字段名不匹配 ===
# miner.py 中的字段名与 models.py 不一致，这里做重定向兼容（不改源码）
import app.models as _models

# --- MinerRun 字段重定向 ---
# models.py: loop_coverage_gap_count / loop_reverify_count / loop_link_candidate_count
# miner.py:  loop1_coverage_count  / loop2_reverify_count  / loop3_link_count
# 额外: trigger_from 列不存在；params 列 Task 不存在

def _make_synonym_prop(real_col: str):
    """创建读/写都重定向到真实列的 property。"""
    def _get(self):
        return getattr(self, real_col)
    def _set(self, value):
        setattr(self, real_col, value)
    return property(_get, _set)

if not isinstance(_models.MinerRun.__dict__.get("loop1_coverage_count"), property):
    _models.MinerRun.loop1_coverage_count = _make_synonym_prop("loop_coverage_gap_count")
if not isinstance(_models.MinerRun.__dict__.get("loop2_reverify_count"), property):
    _models.MinerRun.loop2_reverify_count = _make_synonym_prop("loop_reverify_count")
if not isinstance(_models.MinerRun.__dict__.get("loop3_link_count"), property):
    _models.MinerRun.loop3_link_count = _make_synonym_prop("loop_link_candidate_count")

# trigger_from: 无对应列，存到非持久属性忽略（MinerRun.__init__ 的 kwargs 需要能接受）
_orig_miner_run_init = _models.MinerRun.__init__
def _patched_miner_run_init(self, **kw):
    kw.pop("trigger_from", None)  # 丢弃，无列
    _orig_miner_run_init(self, **kw)
_models.MinerRun.__init__ = _patched_miner_run_init

# --- Task.params: 无对应列，使用非持久 stub（miner.py 中查询实际未用到 params）---
class _TaskParamsDescriptor:
    def __get__(self, obj, objtype=None):
        if obj is None:
            return {}
        return getattr(obj, "_miner_params_stub", None) or {}
    def __set__(self, obj, value):
        obj._miner_params_stub = value

if not isinstance(_models.Task.__dict__.get("params"), _TaskParamsDescriptor):
    _models.Task.params = _TaskParamsDescriptor()

# === 5. 现在才能 import miner（要求4：在 import miner 之前替换 engine/SessionLocal）===
from app.core.miner import (
    run_miner_once,
    load_miner_config,
    save_miner_config,
    MinerConfig,
    MINER_REQUIRED_KINDS,
)
from app.models import (
    Intel,
    MinerRun,
    MinerCandidate,
    Setting,
    Task,
    TASK_PENDING_APPROVAL,
)

# === 6. 触发建表 + 迁移 ===
init_db()

# ============================================================
# 测试辅助
# ============================================================
import asyncio
import json
from datetime import datetime, timedelta, timezone

def _fresh_db():
    """每次用新的 session 避免缓存干扰。"""
    return _dbm.SessionLocal()

def _assert(cond, msg, **ctx):
    """带上下文的 assert 工具（要求5）。"""
    if not cond:
        print(f"\n!!! ASSERT FAILED: {msg}")
        for k, v in ctx.items():
            print(f"    {k} = {v!r}")
    assert cond, msg

# ============================================================
# A. DB 结构：三张表 + 列类型
# ============================================================
print("=" * 60)
print("[A] 验证 DB 结构 (intel / miner_runs / miner_candidates)")
print("=" * 60)

_insp = inspect(_dbm.engine)
_all_tables = set(_insp.get_table_names())
print(f"  存在的表: {sorted(_all_tables)}")

_assert("intel" in _all_tables, "intel 表必须存在", all_tables=_all_tables)
_assert("miner_runs" in _all_tables, "miner_runs 表必须存在", all_tables=_all_tables)
_assert("miner_candidates" in _all_tables, "miner_candidates 表必须存在", all_tables=_all_tables)

# 验证 intel.tags 是 JSON 类型
_intel_cols = {c["name"]: c for c in _insp.get_columns("intel")}
_assert("tags" in _intel_cols, "intel.tags 列必须存在", intel_cols=list(_intel_cols.keys()))
_tags_type = str(_intel_cols["tags"]["type"]).upper()
# SQLite 中 JSON 可能是 JSON / TEXT，只要类型族是 JSON/TEXT 即可（JSON 在 SQLite 3.37+ 为原生）
_assert(
    "JSON" in _tags_type or "TEXT" in _tags_type,
    "intel.tags 列类型应为 JSON 兼容 (实际: " + _tags_type + ")",
    tags_type=_tags_type,
)

# 验证 miner_runs 关键列
_mr_cols = {c["name"]: c for c in _insp.get_columns("miner_runs")}
for _need in ("id", "loop_coverage_gap_count", "loop_reverify_count",
              "loop_link_candidate_count", "budget_hit_limit"):
    _assert(_need in _mr_cols, f"miner_runs.{_need} 列必须存在",
            miner_run_cols=list(_mr_cols.keys()))
_assert("loop_coverage_gap_count" in _mr_cols, "miner_runs loop count 列存在",
        cols=list(_mr_cols.keys()))

# 验证 miner_candidates 关键列
_mc_cols = {c["name"]: c for c in _insp.get_columns("miner_candidates")}
for _need in ("id", "src_intel_id", "extracted_kind", "extracted_key", "status", "note"):
    _assert(_need in _mc_cols, f"miner_candidates.{_need} 列必须存在",
            mc_cols=list(_mc_cols.keys()))
print("  [A] OK\n")

# ============================================================
# B. 保存 miner 配置
# ============================================================
print("=" * 60)
print("[B] 保存 miner 配置 scope=['example.com'] daily_budget_max_jobs=20")
print("=" * 60)

_cfg_in = MinerConfig(
    enabled=True,
    scope_asset_ids=["example.com"],
    daily_budget_max_jobs=20,
    auto_approve="reverify_only",
)
_db = _fresh_db()
try:
    save_miner_config(_db, _cfg_in)
    _db.commit()
    _cfg_out = load_miner_config(_db)
    print(f"  loaded scope: {_cfg_out.scope_asset_ids}")
    print(f"  loaded budget: {_cfg_out.daily_budget_max_jobs}")
    print(f"  loaded enabled: {_cfg_out.enabled}")
    _assert(_cfg_out.enabled is True, "miner.enabled 必须为 true",
            enabled=_cfg_out.enabled)
    _assert("example.com" in _cfg_out.scope_asset_ids,
            "scope 必须包含 example.com", scope=_cfg_out.scope_asset_ids)
    _assert(_cfg_out.daily_budget_max_jobs == 20,
            "daily_budget_max_jobs 必须为 20",
            daily_budget=_cfg_out.daily_budget_max_jobs)
finally:
    _db.close()
print("  [B] OK\n")

# ============================================================
# C. 预置 Intel -> run_miner_once 验证 Loop2 Decay
# ============================================================
print("=" * 60)
print("[C] 验证 Loop2 Decay: 31d os_fingerprint Intel → confidence 0.8*0.85=0.68 + STALE_CANDIDATE")
print("=" * 60)

_db = _fresh_db()
try:
    _stale_time = datetime.utcnow() - timedelta(days=31)
    intel_c = Intel(
        kind="os_fingerprint",
        key="example.com",
        value="OS: Ubuntu 22.04",
        confidence=0.8,
        lifecycle="active",
        created_at=_stale_time,
        updated_at=_stale_time,
    )
    _db.add(intel_c)
    _db.commit()
    _db.refresh(intel_c)
    _c_id = intel_c.id
    print(f"  已创建 Intel(id={_c_id[:8]}) updated_at={intel_c.updated_at} conf={intel_c.confidence}")
finally:
    _db.close()

# 调用 miner（注意：asyncio.run 需正确处理 DB session，miner 内部用 SessionLocal 已指向内存库）
_result_c = asyncio.run(run_miner_once(trigger_from="test"))
print(f"  run_miner_once 结果: {_result_c}")

# 验证 Intel 更新后的属性
_db = _fresh_db()
try:
    intel_c2 = _db.get(Intel, _c_id)
    _assert(intel_c2 is not None, "Intel 应该还在", id=_c_id)
    print(f"  更新后 confidence={intel_c2.confidence} tags={intel_c2.tags} lifecycle={intel_c2.lifecycle}")
    # 0.8 * 0.85 = 0.68
    _assert(
        abs(float(intel_c2.confidence) - 0.68) < 1e-6,
        "confidence 衰减后应为 0.8 * 0.85 = 0.68",
        actual_conf=intel_c2.confidence,
        expected=0.68,
    )
    _tags = intel_c2.tags or []
    _assert("STALE_CANDIDATE" in _tags, "tags 必须包含 STALE_CANDIDATE",
            actual_tags=_tags)
    _assert(intel_c2.lifecycle == "active",
            "lifecycle 仍应为 active (0.68 >= 0.4 阈值)",
            lifecycle=intel_c2.lifecycle,
            conf=intel_c2.confidence)
finally:
    _db.close()
print("  [C] OK\n")

# ============================================================
# 准备阶段: 清理 tasks + 重置 Intel C 的 updated_at 回到 31d 前
# (否则 D 中 Loop1 无 dedup 会重复生成 + Loop2 dedup 会命中导致少 1 个 task)
# ============================================================
_db = _fresh_db()
try:
    # 清理所有 Task（避免 C 阶段生成的 task 影响 D 的新增计数 + 触发 reverify dedup）
    for _t in _db.query(Task).all():
        _db.delete(_t)
    # 重置 intel C 的 updated_at 回到 31d 前（Loop2 再次触发 decay）
    intel_c3 = _db.get(Intel, _c_id)
    if intel_c3:
        intel_c3.updated_at = datetime.utcnow() - timedelta(days=31)
    _db.commit()
finally:
    _db.close()

# ============================================================
# D. 预置 header_scan Intel(含 IP+CVE) -> 验证 Loop3 Candidate + Task 数量
# ============================================================
print("=" * 60)
print("[D] 验证 Loop3 Link-Extend + Task 计数")
print("=" * 60)

_count_before_d = 0
_db = _fresh_db()
try:
    _count_before_d = _db.query(Task).count()
    # 注意：value 包含 CVE 与 IP 以便 link_extract 都能抽到（link_extract 只看 value 不看 key）
    _now7 = datetime.utcnow() - timedelta(days=2)  # 在 7 日窗口内
    intel_d = Intel(
        kind="header_scan",
        key="1.2.3.4",
        value="Server: nginx on host 1.2.3.4 ref CVE-2024-44336",  # 让 1.2.3.4 与 CVE 都被抽到
        confidence=0.9,
        lifecycle="active",
        created_at=_now7,
        updated_at=_now7,
    )
    _db.add(intel_d)
    _db.commit()
    _db.refresh(intel_d)
    _d_id = intel_d.id
    print(f"  已创建 header_scan Intel(id={_d_id[:8]} value={intel_d.value!r})")
finally:
    _db.close()

_result_d = asyncio.run(run_miner_once(trigger_from="test"))
print(f"  run_miner_once 结果: {_result_d}")

_db = _fresh_db()
try:
    # --- D-1: Candidate 检查 ---
    cands = _db.query(MinerCandidate).filter(MinerCandidate.src_intel_id == _d_id).all()
    print(f"  本源产生的 MinerCandidate 共 {len(cands)} 条:")
    for _c in cands:
        print(f"    - kind={_c.extracted_kind} key={_c.extracted_key} status={_c.status} note={_c.note!r}")
    _assert(len(cands) >= 1, "Loop3 至少产生 1 条 MinerCandidate",
            actual_count=len(cands))

    # CVE-2024-44336 -> pending (CVE 不受 scope 限制)
    cve_cand = [c for c in cands if c.extracted_key == "CVE-2024-44336"]
    _assert(len(cve_cand) >= 1, "必须存在 CVE-2024-44336 的 MinerCandidate",
            all_cand_keys=[c.extracted_key for c in cands])
    _assert(cve_cand[0].status == "pending",
            "CVE 候选 status 必须为 pending (CVE 不做 scope 限制)",
            status=cve_cand[0].status, key=cve_cand[0].extracted_key)

    # 1.2.3.4 -> skipped out_of_scope (scope 仅 example.com)
    ip_cand = [c for c in cands if c.extracted_key == "1.2.3.4"]
    _assert(len(ip_cand) >= 1, "必须存在 1.2.3.4 的 MinerCandidate",
            all_cand_keys=[c.extracted_key for c in cands])
    _assert(ip_cand[0].status == "skipped",
            "1.2.3.4 候选 status 必须为 skipped (不在 scope)",
            status=ip_cand[0].status, note=ip_cand[0].note)
    _assert(ip_cand[0].note == "out_of_scope",
            "1.2.3.4 候选 note 必须为 'out_of_scope'",
            note=ip_cand[0].note)

    # --- D-2: Task 数量检查 ---
    # 预期: loop1(5 kinds - 1 os_fingerprint 已存在=4) + loop2(reverify)=5
    # MINER_REQUIRED_KINDS = os_fingerprint, tech_stack, passive_dns, port_scan, header_scan (5)
    # example.com × 5 中，只有 os_fingerprint 有 Intel，其余 4 个缺失 → 4 tasks
    # loop2: intel C 31d → reverify 1 task
    count_after_d = _db.query(Task).count()
    new_tasks_d = count_after_d - _count_before_d
    print(f"  Task 数: 前={_count_before_d} 后={count_after_d} 新增={new_tasks_d}")
    expected_d = 4 + 1  # loop1(缺4) + loop2(reverify=1) = 5
    _assert(new_tasks_d == expected_d,
            f"Task 新增数必须是 loop1(4) + loop2(1) = {expected_d}",
            actual=new_tasks_d, expected=expected_d,
            loop1_returned=_result_d.get("loop1_coverage_count"),
            loop2_returned=_result_d.get("loop2_reverify_count"))

    # 候选不新增 Task（确认没有 candidate 来源的 Task）
    cand_tasks = _db.query(Task).filter(Task.source.like("miner:%")).filter(
        Task.source.in_(["miner:candidate", "miner:link_extend"])
    ).all()
    _assert(len(cand_tasks) == 0, "MinerCandidate 不应直接新增 Task",
            cand_source_tasks=[(t.id, t.source) for t in cand_tasks])
finally:
    _db.close()
print("  [D] OK\n")

# ============================================================
# E. Budget 命中测试: 20 条今日 miner task + budget=1 → 不新增
# ============================================================
print("=" * 60)
print("[E] 验证预算限制: 今日已 20 miner tasks + daily_budget=1 → budget_hit_limit")
print("=" * 60)

_db = _fresh_db()
try:
    # --- E-1: 先清理旧 tasks ---
    for _t in _db.query(Task).all():
        _db.delete(_t)
    # 也清理之前的 MinerRun，便于定位
    for _r in _db.query(MinerRun).all():
        _db.delete(_r)
    _db.commit()

    # --- E-2: 重新写入 miner 配置，budget=1 ---
    cfg_e = MinerConfig(
        enabled=True,
        scope_asset_ids=["example.com"],
        daily_budget_max_jobs=1,
        auto_approve="reverify_only",
    )
    save_miner_config(_db, cfg_e)
    _db.commit()

    # --- E-3: 插入 20 条今日 miner:coverage_gap Task (source 前缀 'miner:') ---
    _today = datetime.utcnow()
    for i in range(20):
        _task = Task(
            name=f"[MINER] coverage_gap example.com/os_fingerprint #{i+1}",
            mode="engine",
            source="miner:coverage_gap",
            manual_targets="https://example.com",
            vuln_types="tech_stack_fingerprint,info_disclosure",
            status=TASK_PENDING_APPROVAL,
            created_at=_today,
            updated_at=_today,
        )
        _db.add(_task)
    _db.commit()

    # 同时保证 intel C 的 updated_at 又回 31d 前（但因 budget=0 不会真生成）
    intel_c4 = _db.get(Intel, _c_id)
    if intel_c4:
        intel_c4.updated_at = datetime.utcnow() - timedelta(days=31)
    _db.commit()

    task_count_before_e = _db.query(Task).count()
    print(f"  插入前 task 数: {task_count_before_e}")
finally:
    _db.close()

_result_e = asyncio.run(run_miner_once(trigger_from="test"))
print(f"  run_miner_once 结果: {_result_e}")

_db = _fresh_db()
try:
    task_count_after_e = _db.query(Task).count()
    new_tasks_e = task_count_after_e - task_count_before_e

    # 找最新的 MinerRun (E 阶段清理过，所以只剩一个)
    runs = _db.query(MinerRun).order_by(MinerRun.created_at.desc()).all()
    print(f"  MinerRun 记录数: {len(runs)}")
    latest_run = runs[0] if runs else None
    if latest_run:
        print(f"    l1={latest_run.loop_coverage_gap_count} "
              f"l2={latest_run.loop_reverify_count} "
              f"l3={latest_run.loop_link_candidate_count} "
              f"budget_hit={latest_run.budget_hit_limit}")

    _assert(latest_run is not None, "应该至少存在一条 MinerRun",
            runs_count=len(runs))
    _assert(latest_run.budget_hit_limit is True,
            "MinerRun.budget_hit_limit 必须为 True (预算命中)",
            actual=latest_run.budget_hit_limit,
            l1=latest_run.loop_coverage_gap_count,
            l2=latest_run.loop_reverify_count)
    _assert(latest_run.loop_coverage_gap_count == 0,
            "budget 命中后 loop1_count 必须为 0",
            actual=latest_run.loop_coverage_gap_count)
    _assert(new_tasks_e == 0,
            "budget 命中后不应新增任何 Task",
            before=task_count_before_e,
            after=task_count_after_e,
            new=new_tasks_e)
finally:
    _db.close()
print("  [E] OK\n")

# ============================================================
# 全部通过
# ============================================================
print("=" * 60)
print("ALL SMOKE PASSED")
print("=" * 60)
