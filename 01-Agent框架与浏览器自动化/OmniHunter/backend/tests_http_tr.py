# -*- coding: utf-8 -*-
"""OmniHunter 手工 HTTP TR 验证（运行时需 backend 已经启动）。"""
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_VENDOR = os.path.join(_HERE, "vendor")
for _p in (_HERE, _VENDOR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import httpx  # noqa: E402

BASE = "http://127.0.0.1:18800/api"


def _resp(r: httpx.Response, label: str) -> None:
    hdr = r.headers.get("X-Request-Id", "")
    body_text = r.text
    try:
        body = r.json()
    except Exception:
        body = None
    print(f"\n=== {label} ===")
    print(f"  status: {r.status_code}")
    print(f"  X-Request-Id header: {hdr}")
    if body is not None:
        print(f"  body: {json.dumps(body, ensure_ascii=False)[:600]}")
        brq = ""
        if isinstance(body, dict):
            d = body.get("data") or {}
            if isinstance(d, dict):
                brq = d.get("request_id", "")
        if brq and hdr:
            print(f"  request_id header == body.data.request_id: {brq == hdr}")
    else:
        print(f"  body(raw): {body_text[:400]}")


def _post_task(c: httpx.Client, payload: dict, label: str, retries: int = 6,
               sleep_s: float = 5.0) -> dict:
    """创建任务：sqlite 写锁时重试，避免与后台 Orchestrator 并发冲突。"""
    last = None
    for i in range(retries):
        r = c.post(BASE + "/tasks", json=payload, timeout=15)
        if r.status_code != 500 or "database is locked" not in r.text:
            _resp(r, label)
            return r.json()
        last = r
        print(f"  [{label}] sqlite locked, retry {i+1}/{retries} after {sleep_s}s")
        time.sleep(sleep_s)
    assert last is not None
    _resp(last, label + " (last retry)")
    return last.json()


def main() -> int:
    c = httpx.Client(timeout=15)
    # TR-1.1 health single key
    r = c.get(BASE + "/health")
    _resp(r, "TR-1.1 GET /health (single status key, no version)")
    assert r.status_code == 200
    j = r.json()
    assert list(j.keys()) == ["status"], f"health 泄漏字段: {list(j.keys())}"
    assert j["status"] == "ok"

    # TR-1.2 / TR-1.3 _dbg_boom E-5001 0 traceback
    r = c.get(BASE + "/_dbg_boom")
    _resp(r, "TR-1.2/TR-1.3 _dbg_boom E-5001 + X-Request-Id")
    assert r.status_code == 500, f"expected 500, got {r.status_code}"
    j = r.json()
    assert j.get("data", {}).get("code") == "E-5001"
    assert "Traceback" not in r.text, "响应体不应包含 traceback"
    assert "request-id" in j.get("message", "")
    brq = j["data"]["request_id"]
    hdr = r.headers.get("X-Request-Id", "")
    assert brq == hdr, f"rid mismatch body={brq} hdr={hdr}"

    # TR-2.2 Intel masked + tags
    pl = {
        "kind": "credential_demo_tr",
        "key": "mysql://utr2@ex.com",
        "value": "password=XYZ9&apikey=AK_demo_tr&host=10.1.2.3",
        "lifecycle": "active",
        "confidence": 0.9,
        "source": "manual:tr",
        "tags": ["DEMO_TR", "HELLO"],
    }
    r = c.post(BASE + "/intel", json=pl)
    _resp(r, "TR-2.2 Intel POST masked + tags")
    assert r.status_code == 200, f"got {r.status_code}: {r.text[:400]}"
    j = r.json()
    d = j["data"]
    assert d["masked"] is True, "masked 应为 True (含 password/apikey)"
    assert set(d["tags"]) == {"DEMO_TR", "HELLO"}

    # TR-8.1(a) PUT miner/config enabled=true scope=[] -> 400
    cfg = {"enabled": True, "scope_asset_ids": [], "daily_budget_max_jobs": 20,
           "max_runtime_min": 1440, "auto_approve": "reverify_only",
           "cron_expr": "0 2 * * *"}
    r = c.put(BASE + "/miner/config", json=cfg)
    _resp(r, "TR-8.1(a) enabled=true scope=[] -> 400")
    assert r.status_code == 400, f"期待 400，实际 {r.status_code}: {r.text[:400]}"

    # TR-8.1(b) enabled=false scope=[] -> 200
    cfg2 = dict(cfg); cfg2["enabled"] = False
    r = c.put(BASE + "/miner/config", json=cfg2)
    _resp(r, "TR-8.1(b) enabled=false scope=[] -> 200")
    assert r.status_code == 200, f"got {r.status_code}: {r.text[:400]}"

    # TR-9 Task pending_approval -> approve / reject 流
    tp = {
        "name": "[MINER-HTTP-TR] t9_example",
        "mode": "engine",
        "manual_targets": "http://example.com",  # 公网但不触发深度探测（引擎扫描时会直接探，失败不影响创建流验证）
        "source": "miner:t9_http_tr",
        "status": "pending_approval",
    }
    j1 = _post_task(c, tp, "TR-9a create Task status=pending_approval")
    tid = j1["data"]["id"]
    assert j1["data"]["status"] == "pending_approval", f"创建后 status={j1}"

    # 列表拿
    r = c.get(BASE + "/tasks")
    assert r.status_code == 200
    rows = r.json()
    found = next((x for x in rows if x["id"] == tid), None)
    assert found, "tasks 列表缺少刚创建任务"
    print(f"  TR-9b tasks list row.status={found['status']} (expect pending_approval)")
    assert found["status"] == "pending_approval"

    # 批准
    r = c.post(BASE + f"/tasks/{tid}/approve")
    _resp(r, "TR-9c approve")
    assert r.status_code == 200, f"approve失败: {r.status_code} {r.text[:400]}"
    ap = r.json()
    print(f"  approve message: {ap.get('message')}")

    # 等后台写锁释放后，再创建第二条拒绝用（avoid sqlite locked）
    time.sleep(6)
    tp2 = dict(tp); tp2["name"] = "[MINER-HTTP-TR] t9_reject"; tp2["manual_targets"] = "http://httpbin.org"
    j2 = _post_task(c, tp2, "TR-9d create pending_approval (to reject)")
    tid2 = j2["data"]["id"]
    assert j2["data"]["status"] == "pending_approval", f"创建第二个任务 状态非 pending_approval: {j2}"
    r = c.post(BASE + f"/tasks/{tid2}/reject")
    _resp(r, "TR-9e reject")
    assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
    jre = r.json(); print(f"  reject message: {jre.get('message')}")
    # 确认 reject 后再 approve -> 400
    r = c.post(BASE + f"/tasks/{tid2}/approve")
    _resp(r, "TR-9f reject后再approve 期待400")
    assert r.status_code == 400

    # TR-2.1 api_docs_enabled=false 重启验证(需重启，这里只验证默认200，用 Setting 写入后用 GET /openapi.json 验证当前没生效（因为 FastAPI 构造期读的）——通过 Setting 保存成功并确认路径可读。
    r = c.put(BASE + "/settings", json={"key": "api_docs_enabled", "value": "false"})
    _resp(r, "TR-2.1(partial) 写入 Setting api_docs_enabled=false（需重启生效）")
    print("  TR-2.1 已写入 Setting，重启后 /docs /openapi.json 才会 404（FastAPI 构造期读取）")

    # GET /miner/runs 审计日志存在
    r = c.get(BASE + "/miner/runs")
    _resp(r, "GET /miner/runs 存在")
    assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"

    print("\n\nALL HTTP TR PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
