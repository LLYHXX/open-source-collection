# -*- coding: utf-8 -*-
"""MCP 接入 + 技能包 离线自动化测试（不依赖网络与真实 MCP server）。

运行：cd backend && set PYTHONPATH=.;vendor && python tests_mcp_skillpack.py
覆盖：
  1. MCPStdioClient 与假 stdio MCP server 握手/发现/调用
  2. MCPManager.load_into_registry 注入 ToolRegistry（含不可用服务器占位）
  3. 技能包本地安装校验 + prompt_suffix 汇总
"""
import json
import os
import sys
import tempfile
from pathlib import Path

# 独立测试库，避免污染真实数据
_TMP = tempfile.mkdtemp(prefix="mcp_test_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "test.db").replace("\\", "/")

sys.path.insert(0, ".")
sys.path.insert(0, "vendor")

FAKE_SERVER = r'''
import json, sys
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except Exception:
        continue
    method = msg.get("method", "")
    rid = msg.get("id")
    if method == "initialize":
        print(json.dumps({"jsonrpc": "2.0", "id": rid,
                          "result": {"protocolVersion": "2024-11-05",
                                     "serverInfo": {"name": "fake", "version": "0.1"}}}), flush=True)
    elif method == "tools/list":
        print(json.dumps({"jsonrpc": "2.0", "id": rid, "result": {"tools": [
            {"name": "echo", "description": "回显文本",
             "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
            {"name": "add", "description": "加法",
             "inputSchema": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}}},
        ]}}), flush=True)
    elif method == "tools/call":
        name = msg["params"]["name"]
        args = msg["params"].get("arguments") or {}
        if name == "echo":
            out = f"echo: {args.get('text', '')}"
        elif name == "add":
            out = str(args.get("a", 0) + args.get("b", 0))
        else:
            out = ""
        print(json.dumps({"jsonrpc": "2.0", "id": rid, "result": {
            "content": [{"type": "text", "text": out}]}}), flush=True)
'''

PASS, FAIL = 0, []


def check(name, cond, detail=""):
    global PASS
    if cond:
        PASS += 1
        print(f"[PASS] {name}")
    else:
        FAIL.append(name)
        print(f"[FAIL] {name} {detail}")


def main():
    from app.core.mcp_client import MCPStdioClient
    from app.core.mcp_manager import MCPManager
    from app.core.tool_registry import ToolRegistry

    # 写假 server 脚本
    server_path = Path(_TMP) / "fake_mcp_server.py"
    server_path.write_text(FAKE_SERVER, encoding="utf-8")

    # ===== 1. 客户端三步协议 =====
    client = MCPStdioClient(sys.executable, [str(server_path)])
    info = client.initialize()
    check("MCP 握手 initialize", info.get("serverInfo", {}).get("name") == "fake")
    tools = client.list_tools()
    check("MCP 工具发现 tools/list", [t["name"] for t in tools] == ["echo", "add"])
    out = client.call_tool("echo", {"text": "hello"})
    check("MCP 工具调用 echo", out == "echo: hello", f"got={out!r}")
    out2 = client.call_tool("add", {"a": 2, "b": 3})
    check("MCP 工具调用 add", out2 == "5", f"got={out2!r}")

    # ===== 2. 注册表注入 =====
    import app.models  # noqa: F401  # 先注册模型再建表
    from app.database import Base, SessionLocal, engine
    Base.metadata.create_all(engine)
    from app.models import MCPServer, SkillPack

    db = SessionLocal()
    try:
        db.add(MCPServer(name="demo", command=sys.executable,
                         args=json.dumps([str(server_path)]),
                         env="{}", enabled=True))
        # 不可用服务器：占位工具 + 状态回写
        db.add(MCPServer(name="bad", command="definitely_not_exist_xyz",
                         args="[]", env="{}", enabled=True))
        db.commit()

        reg = ToolRegistry()
        mgr = MCPManager()
        n = mgr.load_into_registry(reg, db)
        check("load_into_registry 注册数=2", n == 2, f"n={n}")
        check("demo 工具已注入", reg.has("mcp__demo__echo") and reg.has("mcp__demo__add"))
        r = reg.execute("mcp__demo__echo", {"text": "hi"})
        check("registry 执行 MCP 工具", r == "echo: hi", f"got={r!r}")
        check("bad 服务器占位工具", reg.has("mcp__bad__unavailable"))
        bad = db.query(MCPServer).filter(MCPServer.name == "bad").first()
        check("bad 状态回写连接失败", bad.status == "连接失败", f"status={bad.status}")
        demo = db.query(MCPServer).filter(MCPServer.name == "demo").first()
        check("demo 工具数回写", demo.tool_count == 2 and demo.status == "已连接")
        schema_ok = any(s["function"]["name"] == "mcp__demo__echo"
                        and s["function"]["parameters"].get("properties")
                        for s in reg.schemas())
        check("OpenAI schema 透传", schema_ok)
    finally:
        db.close()
    mgr.shutdown_all()
    client.close()

    # ===== 3. 技能包 =====
    from app.core import skillpacks as sp

    pack_dir = Path(_TMP) / "my-pack"
    (pack_dir / "prompts").mkdir(parents=True)
    (pack_dir / "skillpack.json").write_text(json.dumps({
        "name": "nuclei-master", "version": "1.2.0",
        "description": "nuclei 战术包",
        "prompts": {"worker": "prompts/recon.md"},
        "recipes": [{"name": "全模板扫描", "templates": "cves"}],
    }, ensure_ascii=False), encoding="utf-8")
    (pack_dir / "prompts" / "recon.md").write_text(
        "# 战术：优先跑 nuclei cves 模板，再手工验证。", encoding="utf-8")

    manifest, dst = sp.install_from_local(str(pack_dir))
    check("技能包本地安装", manifest["name"] == "nuclei-master" and dst.is_dir())

    # 非法包被拒：缺 prompts
    bad_dir = Path(_TMP) / "bad-pack"
    bad_dir.mkdir(parents=True)
    (bad_dir / "skillpack.json").write_text('{"name": "bad"}', encoding="utf-8")
    try:
        sp.install_from_local(str(bad_dir))
        check("非法包校验拒绝", False)
    except sp.SkillPackError:
        check("非法包校验拒绝", True)

    # 注入提示词
    db = SessionLocal()
    try:
        db.add(SkillPack(name=manifest["name"], version=manifest["version"],
                         description=manifest["description"],
                         source="local", path=str(dst),
                         manifest=json.dumps(manifest, ensure_ascii=False),
                         enabled=True))
        db.commit()
        suffix = sp.prompt_suffix(db)
        check("prompt_suffix 含包内容", "nuclei cves" in suffix and "nuclei-master" in suffix)
        empty = sp.prompt_suffix(db, roles=("report",))
        check("按角色过滤为空", empty == "")
    finally:
        db.close()

    print(f"\n===== 结果: {PASS} PASS / {len(FAIL)} FAIL =====")
    if FAIL:
        for f in FAIL:
            print("  FAIL:", f)
        sys.exit(1)


if __name__ == "__main__":
    main()
