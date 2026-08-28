"""前端加密参数处理工具（解决 3DES/AES 等前端加密导致流量变异失效）。

用户痛点（河北大学 3DES 案例）：抓到的请求参数是密文，直接变异密文
服务端解密失败 → 流量变异完全失效。需要完整的「解密→明文变异→重加密」链路。

两套方案合一（用户设计要点）：

方案 A - 静态 AST 提取（适合未混淆/轻度混淆代码）：
  analyze_crypto_js(js_url_or_path) -> 用正则+轻量 AST 识别
  CryptoJS/forge 等加密库调用，提取 key/iv/算法/mode/padding。
  支持 CryptoJS.AES.encrypt / CryptoJS.DES.encrypt / forge.cipher.create
  等常见模式。

方案 B - 动态 JS Hook（适合混淆代码，不破解算法）：
  generate_js_hook(crypto_func_name, mutation_value) -> 生成一段
  mitmproxy 注入的 JS 脚本，Hook 前端加密函数（如 desEncrypt），
  在明文阶段直接替换成变异值，让前端原生加密逻辑自己算密文，
  100% 还原加密效果。

方案 C - 离线解密重加密（适合已知 key 的简单算法）：
  decrypt_and_reencrypt(ciphertext, key, algo, mode, padding, mutation)
  -> 用 Python pycryptodome 解密→明文变异→重加密→返回新密文。
  需装 pycryptodome 到 vendor。
"""
import base64
import re


# ===== 方案 A：静态 AST 提取 =====

# CryptoJS / forge 常见加密调用模式（正则匹配，轻量无需真 AST 库）
_CRYPTO_PATTERNS: list[dict] = [
    # CryptoJS.AES.encrypt(plaintext, key, {iv, mode, padding})
    {"library": "CryptoJS", "algo": "AES",
     "regex": r"CryptoJS\.AES\.encrypt\s*\(\s*([^,]+),\s*([^,]+)"
              r"(?:\s*,\s*\{([^}]*)\})?"},
    {"library": "CryptoJS", "algo": "DES",
     "regex": r"CryptoJS\.DES\.encrypt\s*\(\s*([^,]+),\s*([^,]+)"
              r"(?:\s*,\s*\{([^}]*)\})?"},
    {"library": "CryptoJS", "algo": "3DES",
     "regex": r"CryptoJS\.TripleDES\.encrypt\s*\(\s*([^,]+),\s*([^,]+)"
              r"(?:\s*,\s*\{([^}]*)\})?"},
    {"library": "CryptoJS", "algo": "Rabbit",
     "regex": r"CryptoJS\.Rabbit\.encrypt\s*\(\s*([^,]+),\s*([^,]+)"},
    {"library": "CryptoJS", "algo": "RC4",
     "regex": r"CryptoJS\.RC4\.encrypt\s*\(\s*([^,]+),\s*([^,]+)"},
    # forge.cipher.createCipher('AES-CBC', key)
    {"library": "forge", "algo": "AES-CBC",
     "regex": r"forge\.cipher\.createCipher\s*\(\s*['\"]([^'\"]+)['\"]"
              r"\s*,\s*([^)]+)\)"},
    {"library": "forge", "algo": "AES-GCM",
     "regex": r"forge\.cipher\.createCipher\s*\(\s*['\"]AES-GCM['\"]"
              r"\s*,\s*([^)]+)\)"},
    # 自定义 desEncrypt/encrypt 函数（用户提到的河北大学案例）
    {"library": "custom", "algo": "unknown",
     "regex": r"(?:function\s+)?(desEncrypt|encryptData|doEncrypt|"
              r"aesEncrypt|encryptParam)\s*\(\s*([^)]*)\)"},
]

# 从 options 块提取 iv/mode/padding
_OPT_PATTERNS = {
    "iv": r"iv\s*:\s*CryptoJS\.enc\.Utf8\.parse\s*\(\s*['\"]([^'\"]+)['\"]",
    "mode": r"mode\s*:\s*CryptoJS\.mode\.(\w+)",
    "padding": r"padding\s*:\s*CryptoJS\.pad\.(\w+)",
}


def analyze_crypto_js(js_source: str) -> str:
    """静态分析前端 JS，识别加密调用 + 提取 key/iv/算法/mode/padding。

    js_source 传 JS 源码字符串（前端抓到的 .js 文件内容）。
    返回识别到的加密调用清单，供 Attacker 决策用哪种变异方案。
    """
    if not js_source or not js_source.strip():
        return "JS 源码为空。"

    findings: list[dict] = []
    for pat in _CRYPTO_PATTERNS:
        for m in re.finditer(pat["regex"], js_source, re.MULTILINE):
            finding = {
                "library": pat["library"], "algo": pat["algo"],
                "plaintext_arg": m.group(1).strip()[:80],
                "key_arg": m.group(2).strip()[:80] if m.lastindex and m.lastindex >= 2 else "",
                "options": {},
                "location": m.start(),
            }
            # 解析 options 块（第三个捕获组）
            if m.lastindex and m.lastindex >= 3:
                opts = m.group(3) or ""
                for k, pat_re in _OPT_PATTERNS.items():
                    om = re.search(pat_re, opts)
                    if om:
                        finding["options"][k] = om.group(1)
            findings.append(finding)

    if not findings:
        return ("未识别到加密调用。可能：1)未用 CryptoJS/forge；"
                "2)重度混淆；3)用 WebCrypto API。"
                "建议用 generate_js_hook 动态 Hook 方案。")

    lines = [f"== analyze_crypto_js 识别 {len(findings)} 处加密调用 =="]
    for i, f in enumerate(findings):
        lines.append(f"  [{i+1}] {f['library']}.{f['algo']} "
                     f"plaintext={f['plaintext_arg']} key={f['key_arg']}")
        if f["options"]:
            opts_str = " ".join(f"{k}={v}" for k, v in f["options"].items())
            lines.append(f"      options: {opts_str}")
        lines.append(f"      location: char_offset={f['location']}")
    lines.append("\n建议：若 key 为字面量，用 decrypt_and_reencrypt 离线重加密；"
                 "若 key 动态或混淆，用 generate_js_hook 动态 Hook。")
    return "\n".join(lines)


# ===== 方案 B：动态 JS Hook 脚本生成 =====

_HOOK_TEMPLATE = """// OmniHunter 自动生成 - Hook 前端加密函数实现明文变异
// 注入方式：mitmproxy --inline-script this_file.py，或浏览器 DevTools 粘贴
(function() {
    var TARGET_FN = "{func_name}";
    var MUTATION = {mutation_json};
    var HIT_COUNT = 0;
    var MAX_HITS = 100;

    function applyMutation(plaintext) {{
        if (typeof plaintext !== 'string') plaintext = String(plaintext);
        // MUTATION 是 {{find: "1001", replace: "1002"}} 或 {{append: "&admin=1"}}
        if (MUTATION.find && MUTATION.replace) {{
            return plaintext.replace(MUTATION.find, MUTATION.replace);
        }}
        if (MUTATION.append) {{
            return plaintext + MUTATION.append;
        }}
        if (MUTATION.replace_all_with) {{
            return MUTATION.replace_all_with;
        }}
        return plaintext;
    }}

    // 等待目标函数定义后包装
    function wrapTarget() {{
        var targetObj = window;
        var parts = TARGET_FN.split('.');
        for (var i = 0; i < parts.length - 1; i++) {{
            if (!targetObj[parts[i]]) return false;
            targetObj = targetObj[parts[i]];
        }}
        var lastPart = parts[parts.length - 1];
        if (typeof targetObj[lastPart] !== 'function') return false;

        var original = targetObj[lastPart];
        targetObj[lastPart] = function() {{
            var plaintext = arguments[0];
            if (HIT_COUNT < MAX_HITS) {{
                var mutated = applyMutation(plaintext);
                if (mutated !== plaintext) {{
                    console.log('[OmniHunter Hook] ' + TARGET_FN +
                                ' plaintext mutated: ' + plaintext +
                                ' -> ' + mutated);
                    arguments[0] = mutated;
                    HIT_COUNT++;
                }}
            }}
            return original.apply(this, arguments);
        }};
        console.log('[OmniHunter Hook] wrapped ' + TARGET_FN);
        return true;
    }}

    // 轮询等待函数就绪（混淆代码可能延迟定义）
    var attempts = 0;
    var timer = setInterval(function() {{
        if (wrapTarget() || attempts++ > 50) {{
            clearInterval(timer);
        }}
    }}, 100);
})();
"""


def generate_js_hook(crypto_func_name: str, mutation: dict) -> str:
    """生成动态 JS Hook 脚本（适合重度混淆代码，不破解算法）。

    crypto_func_name : 前端加密函数全名（如 'desEncrypt' / 'CryptoJS.AES.encrypt'）
    mutation         : 变异指令，支持：
      {"find": "1001", "replace": "1002"}   - 明文中找替换（越权改 ID）
      {"append": "&role=admin"}              - 明文末尾追加（参数注入）
      {"replace_all_with": "admin' OR 1=1--"} - 整体替换（SQLi 等）

    生成的脚本注入 mitmproxy 或浏览器后，会在加密前修改明文，
    让前端原生加密逻辑算密文，100% 还原加密效果。
    """
    import json
    if not crypto_func_name:
        return "请提供要 Hook 的前端加密函数名（如 desEncrypt）。"
    if not isinstance(mutation, dict) or not mutation:
        mutation = {"find": "", "replace": ""}

    script = _HOOK_TEMPLATE.format(
        func_name=crypto_func_name,
        mutation_json=json.dumps(mutation, ensure_ascii=False))
    return (f"== generate_js_hook {crypto_func_name} ==\n"
            f"变异指令: {mutation}\n"
            f"注入方式：mitmproxy --inline-script hook.py，"
            f"或浏览器 DevTools Console 粘贴运行\n\n"
            f"{script}")


# ===== 方案 C：离线解密重加密（已知 key 的简单算法）=====

def decrypt_and_reencrypt(ciphertext: str, key: str, algo: str = "AES",
                            mode: str = "CBC", padding: str = "Pkcs7",
                            iv: str = "", mutation: dict | None = None) -> str:
    """离线解密 → 明文变异 → 重加密（需 pycryptodome）。

    适合已知 key/iv 的简单对称加密（如 3DES/AES-CBC）。
    mutation 同 generate_js_hook 的变异指令。
    返回重加密后的 base64 密文。
    """
    try:
        from Crypto.Cipher import AES, DES3  # type: ignore
        from Crypto.Util.Padding import pad, unpad  # type: ignore
    except ImportError:
        return ("pycryptodome 未安装。"
                "安装: python -m pip install --target=vendor pycryptodome")

    if not ciphertext or not key:
        return "请提供密文与密钥。"

    algo = algo.upper()
    mode = mode.upper()

    # key 字节处理（CryptoJS 默认 Utf8 编码）
    key_bytes = key.encode("utf-8") if isinstance(key, str) else key
    iv_bytes = (iv.encode("utf-8") if iv else b"")

    # 解密
    try:
        if algo == "AES":
            # AES key 必须 16/24/32 字节
            key_bytes = _pad_key(key_bytes, [16, 24, 32])
            if not iv_bytes:
                iv_bytes = b"\x00" * 16
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        elif algo in ("3DES", "TRIPLEDES", "DES3"):
            key_bytes = _pad_key(key_bytes, [24])
            if not iv_bytes:
                iv_bytes = b"\x00" * 8
            cipher = DES3.new(key_bytes, DES3.MODE_CBC, iv_bytes)
        elif algo == "DES":
            key_bytes = _pad_key(key_bytes, [8])
            if not iv_bytes:
                iv_bytes = b"\x00" * 8
            from Crypto.Cipher import DES  # type: ignore
            cipher = DES.new(key_bytes, DES.MODE_CBC, iv_bytes)
        else:
            return f"暂不支持算法: {algo}（支持 AES/3DES/DES）"
    except Exception as e:  # noqa: BLE001
        return f"加密算法初始化失败: {e}"

    # 密文解码（base64 或 hex）
    try:
        ct_bytes = base64.b64decode(ciphertext)
    except Exception:  # noqa: BLE001
        try:
            ct_bytes = bytes.fromhex(ciphertext)
        except Exception:  # noqa: BLE001
            return "密文既非 base64 也非 hex，无法解码。"

    try:
        plaintext_padded = cipher.decrypt(ct_bytes)
        plaintext = unpad(plaintext_padded, cipher.block_size)
    except Exception as e:  # noqa: BLE001
        return (f"解密失败（key/iv/mode 不对，或密文损坏）: {e}")

    plaintext_str = plaintext.decode("utf-8", errors="ignore")

    # 明文变异
    mutated = plaintext_str
    if isinstance(mutation, dict):
        if mutation.get("find") and mutation.get("replace"):
            mutated = plaintext_str.replace(mutation["find"],
                                            mutation["replace"])
        elif mutation.get("append"):
            mutated = plaintext_str + mutation["append"]
        elif mutation.get("replace_all_with"):
            mutated = mutation["replace_all_with"]

    if mutated == plaintext_str:
        return (f"解密成功明文: {plaintext_str[:200]}\n"
                f"未应用变异（mutation 为空或未匹配）。")

    # 重加密
    try:
        mutated_bytes = mutated.encode("utf-8")
        padded = pad(mutated_bytes, cipher.block_size)
        # 重新构造 cipher（IV 重用）
        if algo == "AES":
            cipher2 = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        elif algo in ("3DES", "TRIPLEDES", "DES3"):
            cipher2 = DES3.new(key_bytes, DES3.MODE_CBC, iv_bytes)
        else:
            from Crypto.Cipher import DES  # type: ignore
            cipher2 = DES.new(key_bytes, DES.MODE_CBC, iv_bytes)
        new_ct = cipher2.encrypt(padded)
        new_ct_b64 = base64.b64encode(new_ct).decode("ascii")
    except Exception as e:  # noqa: BLE001
        return f"重加密失败: {e}"

    return (f"== decrypt_and_reencrypt 成功 ==\n"
            f"原明文: {plaintext_str[:200]}\n"
            f"变异后: {mutated[:200]}\n"
            f"新密文(base64): {new_ct_b64[:300]}")


def _pad_key(key_bytes: bytes, valid_lengths: list[int]) -> bytes:
    """把 key 补齐到合法长度（CryptoJS Utf8 parse 后可能任意长）。"""
    for n in valid_lengths:
        if len(key_bytes) <= n:
            return key_bytes.ljust(n, b"\x00")
    # 超长则截断到最大合法长度
    return key_bytes[:valid_lengths[-1]]
