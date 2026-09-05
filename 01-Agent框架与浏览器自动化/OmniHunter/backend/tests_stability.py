# -*- coding: utf-8 -*-
"""后端稳定性实测：报告提交/裁决/并发写/miner trigger/WAL 全链路。"""
import json
import os
import sys
import threading
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, os.path.join(_HERE, "vendor")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import httpx  # noqa: E402

BASE = "http://127.0.0.1:18800/api"
_fails = []


def check(name: str, cond: bool, detail: str = "") -> None:
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {name}" + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        _fails.append(name)


def main() -> int:
    c = httpx.Client(timeout=60)

    # 0. 健康
    r = c.get(BASE + "/health")
    check("health 200 单键", r.status_code == 200 and set(r.json().keys()) == {"status"})

    # 1. WAL 模式验证（DB 文件应出现 -wal）
    db_path = os.path.join(_HERE, "data", "aififteen_hunter.db")
    wal_path = db_path + "-wal"
    # 触发一次写让 WAL 落地
    c.get(BASE + "/vulns")
    time.sleep(0.5)
    check("SQLite WAL 已启用(出现 -wal 文件或 journal_mode=wal)",
          os.path.exists(wal_path) or _journal_is_wal(db_path),
          f"wal_exists={os.path.exists(wal_path)}")

    # 2. 报告生成（用户"确认报告提交"核心动作）——先建任务+漏洞
    tp = {"name": "[STAB] report-test", "mode": "engine",
          "manual_targets": "http://example.com", "source": "manual:stab"}
    r = c.post(BASE + "/tasks", json=tp)
    check("建任务 200", r.status_code == 200, r.text[:300])
    tid = r.json()["data"]["id"]

    # 直接插一条漏洞走引擎不现实，这里用 reports/generate 对空漏洞也应稳定出报告
    r = c.post(BASE + "/reports/generate", json={"task_id": tid})
    check("报告生成 200（空漏洞也不崩）", r.status_code == 200, r.text[:300])
    if r.status_code == 200:
        rep = r.json()["data"]["report"]
        check("报告含模板名与正文", bool(rep) and "漏洞报告" in rep, rep[:120])

    # 3. 坏模板语法 → 期望 400 友好提示而非 500
    r = c.post(BASE + "/reports/templates",
               json={"name": "[STAB]bad", "content": "{% for v in vulns %}{{ v.x ",
                     "is_default": False})
    if r.status_code == 200:
        bad_tid = r.json()["data"]["id"]
        r2 = c.post(BASE + "/reports/generate",
                    json={"task_id": tid, "template_id": bad_tid})
        check("坏 jinja2 模板返回 400（非 500 崩溃）", r2.status_code == 400,
              f"status={r2.status_code} body={r2.text[:200]}")
        c.delete(BASE + f"/reports/templates/{bad_tid}")
    else:
        check("坏模板建模板接口", False, r.text[:200])

    # 4. 并发写：8 个线程同时 POST intel（含 password 触发 masked），全部应成功无 locked
    def _write_intel(i):
        try:
            rr = httpx.post(BASE + "/intel", timeout=60, json={
                "kind": "stab_concurrent", "key": f"host{i}.example.com",
                "value": f"password=secret{i}&apikey=AK_{i}", "lifecycle": "active",
                "confidence": 0.7, "source": f"stab:conc{i}", "tags": [f"T{i}"]})
            return rr.status_code
        except Exception as e:  # noqa: BLE001
            return f"EXC:{e}"

    results = []
    threads = [threading.Thread(target=lambda i=i: results.append(_write_intel(i)))
               for i in range(8)]
    t0 = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    ok = sum(1 for x in results if x == 200)
    locked = [x for x in results if x != 200]
    check(f"8 并发 intel 写入全部成功（WAL 生效，无 database is locked）",
          ok == 8, f"ok={ok}/8 失败={locked} 耗时={time.time()-t0:.1f}s")

    # 5. miner trigger-once（后台）+ GET /runs 读 trigger_from（验证缺列崩溃已修）
    r = c.post(BASE + "/miner/trigger-once")
    check("miner trigger-once 202", r.status_code == 200, r.text[:200])
    time.sleep(3)
    r = c.get(BASE + "/miner/runs?limit=5")
    check("GET /miner/runs 200 且可读 trigger_from（缺列崩溃已修）",
          r.status_code == 200, r.text[:300])
    if r.status_code == 200:
        runs = r.json()["data"]
        check("miner runs 非空且字段齐全",
              len(runs) > 0 and "trigger_from" in (runs[0] if runs else {}),
              f"runs={len(runs)}")

    # 6. 后端进程仍然存活（health 再探一次）
    r = c.get(BASE + "/health")
    check("压测后后端进程仍存活", r.status_code == 200)

    print("\n" + ("=" * 50))
    if _fails:
        print(f"稳定性测试 {len(_fails)} 项失败: {_fails}")
        return 1
    print("稳定性测试全部通过 ✓")
    return 0


def _journal_is_wal(db_path: str) -> bool:
    try:
        import sqlite3
        con = sqlite3.connect(db_path, timeout=5)
        mode = con.execute("PRAGMA journal_mode").fetchone()[0]
        con.close()
        return str(mode).lower() == "wal"
    except Exception:  # noqa: BLE001
        return False


if __name__ == "__main__":
    sys.exit(main())
