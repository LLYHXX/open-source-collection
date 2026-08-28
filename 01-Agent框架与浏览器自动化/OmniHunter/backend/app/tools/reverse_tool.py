"""逆向分析工具（纯 Python 内置版，借鉴 03/逆向工程/reverse-skill）。

不依赖 Cutter/rizin/IDA 等外部二进制，全部用纯 python 库实现：
  - lief      : 解析 PE/ELF/Mach-O，输出架构/节区/导入表/导出表
  - capstone  : 多架构反汇编（x86/arm/mips 等）
  - 正则       : 提取可打印字符串（ASCII + UTF-16LE）

库装到 vendor 目录，启动时由 sitecustomize.py 注入 sys.path。
未安装时返回友好提示而非崩溃，风格对齐 httpx_tool.py。
"""
import re


def binary_info(binary_path: str) -> str:
    """解析二进制文件，输出架构/格式/入口/节区/导入表/导出表摘要。

    支持 PE / ELF / Mach-O（lief 自动识别）。lief 未装返回安装提示。
    """
    if not binary_path:
        return "请提供要分析的二进制文件路径。"
    try:
        import lief  # type: ignore
    except ImportError:
        return ("lief 未安装或未注入 sys.path。"
                "安装: python -m pip install --target=vendor lief，"
                "并确认 backend/sitecustomize.py 已把 vendor 加入 sys.path。")

    try:
        # lief 1.0+: lief.parse 返回 PE/ELF/MachO 子类
        bin_obj = lief.parse(binary_path)
    except Exception as e:  # noqa: BLE001
        return f"lief 解析失败（可能不是有效二进制或格式不支持）: {e}"
    if bin_obj is None:
        return f"lief 无法识别 {binary_path} 的格式（可能不是 PE/ELF/Mach-O）。"

    # 格式与架构（lief 用 __class__ 名判断格式，header 抽架构）
    fmt = type(bin_obj).__name__
    lines: list[str] = [f"== {binary_path} ==", f"format: {fmt}"]

    # 头信息（不同格式字段差异，统一用 getattr 兜底）
    header = getattr(bin_obj, "header", None)
    if header is not None:
        # 架构
        arch = _safe_enum_name(getattr(header, "machine", None),
                              getattr(header, "machine_type", None))
        if arch:
            lines.append(f"arch: {arch}")
        # 入口
        entry = getattr(bin_obj, "entrypoint", None)
        if entry is not None:
            lines.append(f"entry: 0x{entry:x}" if isinstance(entry, int) else f"entry: {entry}")
        # 位宽
        bits = getattr(header, "architecture", None)
        if bits is not None:
            lines.append(f"header_arch_field: {bits}")

    # 节区（PE/ELF/MachO 都有 sections，但 MachO 叫 sections/symbols 略不同）
    sections = getattr(bin_obj, "sections", None) or []
    try:
        secs = list(sections)
    except Exception:  # noqa: BLE001
        secs = []
    if secs:
        lines.append(f"sections({len(secs)}):")
        for s in secs[:40]:
            name = getattr(s, "name", "") or ""
            off = getattr(s, "offset", 0) or 0
            sz = getattr(s, "size", 0) or 0
            ent = getattr(s, "entropy", 0)
            ent_s = f"{ent:.2f}" if isinstance(ent, (int, float)) else "-"
            lines.append(f"  {name[:24]:24} off=0x{off:x} size={sz} entropy={ent_s}")

    # 导入表（聚焦可疑 API：注册表/进程/网络/文件/加密）
    imports = getattr(bin_obj, "imports", None) or []
    try:
        imps = list(imports)
    except Exception:  # noqa: BLE001
        imps = []
    if imps:
        lines.append(f"imports({len(imps)}):")
        # 关键 API 关键词
        sus_keys = ("Reg", "CreateProcess", "ShellExecute", "WinExec",
                    "InternetOpen", "URLDownload", "WSAStartup", "socket",
                    "VirtualAlloc", "WriteProcessMemory", "LoadLibrary",
                    "GetProcAddress", "Crypt", "SetWindowsHook", "CreateService")
        shown = 0
        for imp in imps[:60]:
            name = getattr(imp, "name", "") or ""
            if not name:
                continue
            lib = getattr(imp, "library", "") or ""
            mark = " <==" if any(k in name for k in sus_keys) else ""
            lines.append(f"  {lib}!{name}{mark}")
            shown += 1
            if shown >= 40:
                lines.append(f"  ... 还有 {len(imps) - shown} 条导入未列出")
                break

    # 导出表
    exports = getattr(bin_obj, "exported_functions", None) or getattr(bin_obj, "exports", None) or []
    try:
        exps = list(exports)
    except Exception:  # noqa: BLE001
        exps = []
    if exps:
        lines.append(f"exports({len(exps)}):")
        for e in exps[:20]:
            name = getattr(e, "name", "") or str(e)
            lines.append(f"  {name}")

    return "\n".join(lines)


def disasm(binary_path: str, arch: str = "", start_addr: int = 0,
           count: int = 50) -> str:
    """反汇编二进制，输出指令助记符。

    arch 留空时自动探测（通过 lief 读 header.machine_type）。
    可手动指定：x86 / x64 / arm / arm64 / mips / thumb。
    start_addr 为起始字节偏移（不是 RVA），count 为反汇编条数。
    """
    if not binary_path:
        return "请提供要分析的二进制文件路径。"
    try:
        import capstone  # type: ignore
        import lief  # type: ignore
    except ImportError:
        return ("capstone 或 lief 未安装。"
                "安装: python -m pip install --target=vendor capstone lief")

    # 读二进制字节
    try:
        with open(binary_path, "rb") as f:
            raw = f.read()
    except Exception as e:  # noqa: BLE001
        return f"读取文件失败: {e}"

    # 自动探测架构
    cs_arch, cs_mode, endian_str = _detect_arch(arch, binary_path, lief)
    if cs_arch is None:
        return (f"无法确定反汇编架构。请显式传 arch=x86/x64/arm/arm64/mips/thumb。"
                f"（lief 解析或手动指定 arch 失败）")

    # capstone.CS_ARCH_X86 等常量在 5.x 仍是 int，可直接用
    try:
        md = capstone.Cs(cs_arch, cs_mode)
    except Exception as e:  # noqa: BLE001
        return f"capstone 初始化失败（arch={arch or 'auto'} mode={cs_mode}）: {e}"

    # 取代码段字节：优先 .text 节，否则从 start_addr 取原始字节
    code_bytes, base_addr = _get_code_bytes(binary_path, lief, start_addr, raw)
    if not code_bytes:
        return f"未找到可执行代码段（.text 节或偏移 {start_addr} 处无字节）。"

    lines = [f"== disasm {binary_path} arch={arch or 'auto'} endn={endian_str} "
             f"base=0x{base_addr:x} len={len(code_bytes)} =="]
    n = 0
    for ins in md.disasm(code_bytes, base_addr):
        lines.append(f"0x{ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")
        n += 1
        if n >= count:
            break
    if n == 0:
        return (f"capstone 未反汇编出指令（可能 start_addr 不在代码段，"
                f"或架构探测错误，请显式传 arch=）。")
    return "\n".join(lines)


def extract_strings(binary_path: str, min_len: int = 4) -> str:
    """提取二进制中的可打印字符串（ASCII + UTF-16LE）。

    纯 python 正则实现，无需 lief/capstone。min_len 默认 4。
    返回去重后的字符串清单（按出现顺序），过滤常见无意义填充串。
    """
    if not binary_path:
        return "请提供要分析的二进制文件路径。"
    try:
        with open(binary_path, "rb") as f:
            raw = f.read()
    except Exception as e:  # noqa: BLE001
        return f"读取文件失败: {e}"

    # ASCII 可打印串（0x20-0x7e），长度 >= min_len
    ascii_re = re.compile(rb"[\x20-\x7e]{%d,}" % min_len)
    # UTF-16LE 串：每两字节一字符，第二字节为 0x00，首字节可打印
    utf16_re = re.compile(rb"(?:[\x20-\x7e]\x00){%d,}" % min_len)

    found: list[str] = []
    seen: set[str] = set()
    # 无意义串过滤（填充/对齐/重复字符）
    boring = lambda s: (s.strip(" ._-") == "" or len(set(s)) <= 2
                        or s in (".".join(["x"] * 8), "AAAA"))

    for m in ascii_re.finditer(raw):
        s = m.group().decode("ascii", errors="ignore")
        if not boring(s) and s not in seen:
            seen.add(s)
            found.append(s)
    for m in utf16_re.finditer(raw):
        b = m.group()
        try:
            s = b.decode("utf-16-le")
        except Exception:  # noqa: BLE001
            continue
        if not boring(s) and s not in seen:
            seen.add(s)
            found.append(s)

    if not found:
        return "未提取到可打印字符串（可能已加壳/加密，min_len 太大）。"

    # 突出可疑串：URL/IP/注册表路径/文件扩展名/敏感关键字
    sus_re = re.compile(
        r"(https?://|ftp://|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"[A-Za-z]:\\|HKEY_|HKLM|HKCU|\.dll|\.exe|\.sys|"
        r"cmd\.exe|powershell|/etc/passwd|whoami|admin|password|token)",
        re.IGNORECASE,
    )
    lines = [f"== strings {binary_path} count={len(found)} =="]
    shown = 0
    for s in found[:200]:
        mark = " <==" if sus_re.search(s) else ""
        # 截断过长串
        s_show = s[:120] + "..." if len(s) > 120 else s
        lines.append(f"  {s_show}{mark}")
        shown += 1
    if len(found) > shown:
        lines.append(f"  ... 还有 {len(found) - shown} 条字符串未列出"
                     f"（用 min_len 调整过滤阈值）")
    return "\n".join(lines)


# ===== 内部辅助 =====

def _safe_enum_name(*vals) -> str:
    """lief 的枚举值有 name 属性或 str() 友好显示，统一兜底。"""
    for v in vals:
        if v is None:
            continue
        name = getattr(v, "name", None)
        if name:
            return str(name)
        s = str(v)
        if s and not s.startswith("<"):
            return s
    return ""


def _detect_arch(arch_arg: str, binary_path: str, lief_module):
    """返回 (capstone_arch, capstone_mode, endian_str)。探测失败返回 (None,0,'')。"""
    import capstone  # type: ignore

    arch = (arch_arg or "").lower().strip()

    # 手动指定优先
    manual = {
        "x86": (capstone.CS_ARCH_X86, capstone.CS_MODE_32, "little"),
        "x64": (capstone.CS_ARCH_X86, capstone.CS_MODE_64, "little"),
        "amd64": (capstone.CS_ARCH_X86, capstone.CS_MODE_64, "little"),
        "arm": (capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM, "little"),
        "armbe": (capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM | capstone.CS_MODE_BIG_ENDIAN, "big"),
        "arm64": (capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM, "little"),
        "aarch64": (capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM, "little"),
        "thumb": (capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB, "little"),
        "mips": (capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32, "big"),
        "mipsel": (capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32, "little"),
    }
    if arch in manual:
        return manual[arch]

    # 自动探测：lief 解析后读 header.machine_type
    try:
        bin_obj = lief_module.parse(binary_path)
    except Exception:  # noqa: BLE001
        bin_obj = None
    if bin_obj is None:
        return None, 0, ""

    fmt = type(bin_obj).__name__.lower()
    header = getattr(bin_obj, "header", None)
    mt = getattr(header, "machine", None) or getattr(header, "machine_type", None)
    mt_name = _safe_enum_name(mt).upper() if mt else ""

    if "elf" in fmt:
        if "X86_64" in mt_name or "X64" in mt_name:
            return capstone.CS_ARCH_X86, capstone.CS_MODE_64, "little"
        if "386" in mt_name or "X86" in mt_name or "I386" in mt_name:
            return capstone.CS_ARCH_X86, capstone.CS_MODE_32, "little"
        if "ARM" in mt_name:
            endian = getattr(header, "identity_data", None)
            ed = _safe_enum_name(endian).upper() if endian else ""
            if "LSB" in ed or "LE" in ed:
                return capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM, "little"
            return capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM | capstone.CS_MODE_BIG_ENDIAN, "big"
        if "AARCH64" in mt_name:
            return capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM, "little"
        if "MIPS" in mt_name:
            return capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32, "big"
    elif "pe" in fmt:
        # PE 几乎都是 x86/x64
        if "AMD64" in mt_name or "X64" in mt_name:
            return capstone.CS_ARCH_X86, capstone.CS_MODE_64, "little"
        return capstone.CS_ARCH_X86, capstone.CS_MODE_32, "little"
    elif "macho" in fmt:
        if "X86_64" in mt_name or "X64" in mt_name:
            return capstone.CS_ARCH_X86, capstone.CS_MODE_64, "little"
        if "ARM64" in mt_name or "AARCH64" in mt_name:
            return capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM, "little"
        if "ARM" in mt_name:
            return capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM, "little"
        return capstone.CS_ARCH_X86, capstone.CS_MODE_32, "little"

    return None, 0, ""


def _get_code_bytes(binary_path: str, lief_module, start_addr: int, raw: bytes):
    """取代码段字节与基址。优先 .text 节；否则用 start_addr 偏移取 0x1000 字节。"""
    try:
        bin_obj = lief_module.parse(binary_path)
    except Exception:  # noqa: BLE001
        bin_obj = None

    # 优先从 .text 节取
    if bin_obj is not None:
        secs = getattr(bin_obj, "sections", None) or []
        try:
            for s in secs:
                name = (getattr(s, "name", "") or "").lower()
                if name in (".text", "__text"):  # ELF/PE 用 .text，MachO 用 __text
                    content = getattr(s, "content", None)
                    if content is None:
                        # lief 1.0 部分版本用 bytes() 取
                        try:
                            content = bytes(s)
                        except Exception:  # noqa: BLE001
                            content = None
                    if content:
                        off = getattr(s, "offset", 0) or 0
                        addr = getattr(s, "virtual_address", 0) or off
                        return bytes(content), addr
        except Exception:  # noqa: BLE001
            pass

    # 兜底：从 start_addr 偏移取 0x1000 字节原始数据
    if start_addr < 0 or start_addr >= len(raw):
        return b"", start_addr
    chunk = raw[start_addr:start_addr + 0x1000]
    return chunk, start_addr
