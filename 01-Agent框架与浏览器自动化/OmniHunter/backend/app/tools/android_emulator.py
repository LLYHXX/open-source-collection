"""安卓靶场：Android SDK 模拟器（AVD）全生命周期管理，用于 APP/小程序漏洞挖掘。

设计（Windows 优先，工具为主 · 确定性操作）：
- 环境自检：ANDROID_HOME / %LOCALAPPDATA%\\Android\\Sdk / 内置 backend\\android-sdk 逐级探测
- 一键引导（bootstrap）：自动下载 JDK17 + Android cmdline-tools + platform-tools + emulator
  （写入 license 文件免交互，全程后台 job 进度上报）
- 系统镜像：sdkmanager 安装推荐镜像（google_apis 系可 adb root，便于装 CA 证书）
- AVD 创建：avdmanager + config.ini 定制内存(hw.ramSize)/核心(hw.cpu.ncore)/分辨率/密度
- 启动：emulator 独立进程，可自动挂 mitmproxy 抓包代理（-http-proxy 指向 127.0.0.1:8082）
- 抓包联动：adb root + remount 后把 mitmproxy CA 证书装入系统证书目录（Android 7+ 应用信任）
- APP 管理：adb install / launch / uninstall

所有长操作走后台 job（内存态，带 TTL 淘汰防泄漏）；
所有子进程为确定性命令行调用，不依赖任何 LLM。
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import threading
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any

import httpx

# ===== 用户可控参数白名单（所有进入子进程/adb 的参数必须先过白名单）=====
# .bat 经 cmd /c 执行，& | < > ^ 等 cmd 元字符可被解释为命令分隔符，
# 因此 name/pkg/image 一律用 ASCII 白名单正则校验，杜绝注入
RE_AVD_NAME = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
RE_ADB_PKG = re.compile(r"^[A-Za-z0-9_]+(\.[A-Za-z0-9_\-]+)+$")
RE_ACTIVITY = re.compile(r"^[A-Za-z0-9_.$]+$")
RE_SDK_PKG = re.compile(r"^[A-Za-z0-9;._\-]{1,200}$")

# ===== 常量 =====

# 内置 SDK 目录（bootstrap 默认安装位置）
BUNDLED_SDK_DIR = Path(__file__).resolve().parents[2] / "android-sdk"

CMDLINE_TOOLS_URL = ("https://dl.google.com/android/repository/"
                     "commandlinetools-win-11076708_latest.zip")
JDK_URL = ("https://github.com/adoptium/temurin17-binaries/releases/download/"
           "jdk-17.0.13%2B11/OpenJDK17U-jdk_x64_windows_hotspot_17.0.13_11.zip")

# 推荐系统镜像（google_apis 系支持 adb root）
RECOMMENDED_IMAGES = [
    {"pkg": "system-images;android-30;google_apis;x86_64",
     "label": "Android 11 (默认推荐，兼容性好，可 root)", "size_hint": "~1.6GB"},
    {"pkg": "system-images;android-28;google_apis;x86",
     "label": "Android 9 (老 APP 兼容)", "size_hint": "~1.3GB"},
    {"pkg": "system-images;android-33;google_apis;x86_64",
     "label": "Android 13 (新版本)", "size_hint": "~1.8GB"},
]

# sdkmanager license 文件（写入后免交互）
SDK_LICENSES = {
    "android-sdk-license": "24333f8a63b6825ea9c5514f83c2829b004d1fee",
    "android-sdk-preview-license": "84831b9409646a918e30573bab4c9c91346d8abd",
}

MITMPROXY_CERT = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"

# ===== 后台 job 管理（内存态 + TTL 淘汰，防内存泄漏）=====

_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()
_JOB_TTL = 3600      # 完成后保留 1 小时
_JOB_MAX = 50        # 最多保留 50 个 job


def _job_gc() -> None:
    now = time.time()
    with _jobs_lock:
        done = [jid for jid, j in _jobs.items()
                if j["status"] in ("done", "failed") and now - j["updated_at"] > _JOB_TTL]
        for jid in done:
            _jobs.pop(jid, None)
        if len(_jobs) > _JOB_MAX:
            oldest = sorted(_jobs.items(), key=lambda kv: kv[1]["updated_at"])
            for jid, _ in oldest[: len(_jobs) - _JOB_MAX]:
                _jobs.pop(jid, None)


def job_create(title: str) -> str:
    _job_gc()
    # uuid 生成 jid：同毫秒并发不碰撞，且不可被猜测关联他人 job
    jid = f"job_{uuid.uuid4().hex[:12]}"
    with _jobs_lock:
        _jobs[jid] = {"title": title, "status": "running", "progress": 0,
                      "log": "", "created_at": time.time(), "updated_at": time.time()}
    return jid


def job_update(jid: str, *, status: str | None = None, progress: int | None = None,
               log: str | None = None) -> None:
    with _jobs_lock:
        j = _jobs.get(jid)
        if not j:
            return
        if status:
            j["status"] = status
        if progress is not None:
            j["progress"] = max(0, min(100, int(progress)))
        if log:
            j["log"] = (j["log"] + ("\n" if j["log"] else "") + log)[-8000:]
        j["updated_at"] = time.time()


def job_get(jid: str) -> dict | None:
    with _jobs_lock:
        j = _jobs.get(jid)
        return dict(j) if j else None


# ===== SDK 环境检测 =====

def _sdk_candidates() -> list[Path]:
    out: list[Path] = []
    env = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if env:
        out.append(Path(env))
    out.append(BUNDLED_SDK_DIR)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        out.append(Path(local) / "Android" / "Sdk")
    out.append(Path("C:/Android/Sdk"))
    # 去重保序
    seen, uniq = set(), []
    for p in out:
        rp = str(p.resolve()).lower()
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq


def _find_tool(sdk: Path | None, rel: str) -> Path | None:
    cands: list[Path] = []
    if sdk:
        cands.append(sdk / rel)
    for c in _sdk_candidates():
        cands.append(c / rel)
    for c in cands:
        if c.is_file():
            return c
    return None


def _java_home() -> Path | None:
    """优先内置 jdk（BUNDLED_SDK_DIR/jdk），其次 JAVA_HOME / PATH 探测。"""
    bundled = BUNDLED_SDK_DIR / "jdk"
    if (bundled / "bin" / "java.exe").is_file():
        return bundled
    jh = os.environ.get("JAVA_HOME")
    if jh and (Path(jh) / "bin" / "java.exe").is_file():
        return Path(jh)
    return None


def detect_environment() -> dict:
    """环境自检：SDK/JDK/各工具可用性 + 镜像与 AVD 概况。"""
    sdk = next((c for c in _sdk_candidates() if c.is_dir()), None)
    java = _java_home()
    if java:
        java_ok = True
    else:
        try:
            subprocess.run(["java", "-version"], capture_output=True, timeout=10)
            java_ok = True
        except Exception:  # noqa: BLE001
            java_ok = False
    tools = {
        "sdkmanager": _find_tool(sdk, "cmdline-tools/latest/bin/sdkmanager.bat"),
        "avdmanager": _find_tool(sdk, "cmdline-tools/latest/bin/avdmanager.bat"),
        "adb": _find_tool(sdk, "platform-tools/adb.exe"),
        "emulator": _find_tool(sdk, "emulator/emulator.exe"),
    }
    installed_images = _installed_images(sdk)
    return {
        "sdk_path": str(sdk) if sdk else "",
        "sdk_found": sdk is not None,
        "java_ok": java_ok,
        "java_path": str(java) if java else "",
        "tools": {k: str(v) if v else "" for k, v in tools.items()},
        "tools_ready": all(tools.values()),
        "installed_images": installed_images,
        "recommended_images": RECOMMENDED_IMAGES,
        "avds": list_avds(tools["emulator"]) if tools["emulator"] else [],
        "mitmproxy_cert": str(MITMPROXY_CERT),
        "mitmproxy_cert_exists": MITMPROXY_CERT.is_file(),
    }


def _installed_images(sdk: Path | None) -> list[str]:
    if not sdk:
        return []
    base = sdk / "system-images"
    if not base.is_dir():
        return []
    out = []
    for pkg_dir in sorted(base.rglob("*")):
        if pkg_dir.is_dir() and (pkg_dir / "system" / "system.img").is_file():
            rel = pkg_dir.relative_to(base).as_posix()
            out.append(f"system-images;{rel}")
    return out


# ===== 子进程封装 =====

def _run_bat(bat: Path, args: list[str], timeout: int = 600,
             env_extra: dict | None = None) -> tuple[int, str]:
    """cmd /c 调 .bat（Windows 下 .bat 需经 cmd）。"""
    env = os.environ.copy()
    java = _java_home()
    if java:
        env["JAVA_HOME"] = str(java)
        env["PATH"] = f"{java}\\bin;" + env.get("PATH", "")
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(["cmd", "/c", str(bat), *args],
                          capture_output=True, timeout=timeout, env=env)
    out = (proc.stdout or b"").decode("utf-8", "replace") + \
          (proc.stderr or b"").decode("utf-8", "replace")
    return proc.returncode, out


def _run_exe(exe: Path, args: list[str], timeout: int = 120) -> tuple[int, str]:
    env = os.environ.copy()
    java = _java_home()
    if java:
        env["JAVA_HOME"] = str(java)
    proc = subprocess.run([str(exe), *args], capture_output=True,
                          timeout=timeout, env=env)
    out = (proc.stdout or b"").decode("utf-8", "replace") + \
          (proc.stderr or b"").decode("utf-8", "replace")
    return proc.returncode, out


# ===== 一键引导（JDK + cmdline-tools + platform-tools + emulator）=====

def bootstrap_async(include_emulator: bool = True) -> str:
    jid = job_create("Android SDK 一键引导")
    t = threading.Thread(target=_bootstrap_job, args=(jid, include_emulator),
                         daemon=True, name=f"android-bootstrap-{jid}")
    t.start()
    return jid


def _download(url: str, dest: Path, jid: str, label: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", url, timeout=60, follow_redirects=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0) or 0)
        done = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_bytes(1024 * 256):
                f.write(chunk)
                done += len(chunk)
                if total:
                    job_update(jid, progress=min(99, int(done / total * 100)),
                               log=f"{label}: {done // 1048576}/{total // 1048576} MB")


def _unzip(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(dest)


def _write_licenses(sdk: Path) -> None:
    lic_dir = sdk / "licenses"
    lic_dir.mkdir(parents=True, exist_ok=True)
    for name, digest in SDK_LICENSES.items():
        (lic_dir / name).write_text(digest + "\n", encoding="utf-8")


def _bootstrap_job(jid: str, include_emulator: bool) -> None:
    try:
        sdk = BUNDLED_SDK_DIR
        sdk.mkdir(parents=True, exist_ok=True)

        # 1) JDK（sdkmanager 依赖）
        if not _java_home():
            job_update(jid, log="下载 JDK 17 (Temurin, ~190MB)...")
            jdk_zip = sdk / "_jdk.zip"
            _download(JDK_URL, jdk_zip, jid, "JDK")
            job_update(jid, progress=20, log="解压 JDK...")
            _unzip(jdk_zip, sdk / "_jdk_tmp")
            jdk_zip.unlink(missing_ok=True)
            # Temurin 解压出 jdk-17.x.y+z 目录，规整为 sdk/jdk
            extracted = list((sdk / "_jdk_tmp").glob("jdk-*"))
            if extracted:
                target = sdk / "jdk"
                if target.exists():
                    import shutil
                    shutil.rmtree(target)
                extracted[0].rename(target)
            import shutil as _sh
            _sh.rmtree(sdk / "_jdk_tmp", ignore_errors=True)
            job_update(jid, progress=30, log="JDK 就绪")
        else:
            job_update(jid, progress=30, log="已有 JDK，跳过下载")

        # 2) cmdline-tools
        sm = _find_tool(sdk, "cmdline-tools/latest/bin/sdkmanager.bat")
        if not sm:
            job_update(jid, progress=35, log="下载 Android cmdline-tools (~150MB)...")
            clt_zip = sdk / "_clt.zip"
            _download(CMDLINE_TOOLS_URL, clt_zip, jid, "cmdline-tools")
            job_update(jid, progress=55, log="解压 cmdline-tools...")
            _unzip(clt_zip, sdk / "_clt_tmp")
            clt_zip.unlink(missing_ok=True)
            src = sdk / "_clt_tmp" / "cmdline-tools"
            dst = sdk / "cmdline-tools" / "latest"
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                src.rename(dst)
            import shutil as _sh2
            _sh2.rmtree(sdk / "_clt_tmp", ignore_errors=True)
            _write_licenses(sdk)
        sm = _find_tool(sdk, "cmdline-tools/latest/bin/sdkmanager.bat")
        if not sm:
            raise RuntimeError("cmdline-tools 安装失败")

        # 3) platform-tools + emulator
        pkgs = ["platform-tools"]
        if include_emulator:
            pkgs.append("emulator")
        job_update(jid, progress=60, log=f"sdkmanager 安装 {' '.join(pkgs)} ...")
        code, out = _run_bat(sm, ["--install", *pkgs], timeout=1800)
        if code != 0:
            raise RuntimeError(f"sdkmanager 失败: {out[-500:]}")
        job_update(jid, status="done", progress=100,
                   log="SDK 引导完成：platform-tools/emulator 已就绪。"
                       "下一步请在页面安装系统镜像后创建 AVD。")
    except Exception as e:  # noqa: BLE001
        job_update(jid, status="failed", log=f"引导失败: {e}")


# ===== 系统镜像 =====

def install_image_async(pkg: str) -> str:
    jid = job_create(f"安装系统镜像 {pkg}")
    t = threading.Thread(target=_install_image_job, args=(jid, pkg),
                         daemon=True, name=f"android-image-{jid}")
    t.start()
    return jid


def _install_image_job(jid: str, pkg: str) -> None:
    try:
        if not RE_SDK_PKG.match(pkg):
            raise RuntimeError(f"非法安装包标识: {pkg}")
        sm = _find_tool(None, "cmdline-tools/latest/bin/sdkmanager.bat")
        if not sm:
            raise RuntimeError("SDK 未就绪，请先执行一键引导")
        job_update(jid, log=f"sdkmanager --install {pkg}（体积较大，请耐心等待）...")
        code, out = _run_bat(sm, ["--install", pkg], timeout=3600)
        if code != 0:
            raise RuntimeError(f"镜像安装失败: {out[-500:]}")
        job_update(jid, status="done", progress=100, log=f"镜像 {pkg} 安装完成")
    except Exception as e:  # noqa: BLE001
        job_update(jid, status="failed", log=f"镜像安装失败: {e}")


# ===== AVD 管理 =====

def list_avds(emulator_exe: Path | str | None = None) -> list[str]:
    emu = emulator_exe or _find_tool(None, "emulator/emulator.exe")
    if not emu:
        return []
    try:
        code, out = _run_exe(Path(emu), ["-list-avds"], timeout=30)
        if code != 0:
            return []
        return [ln.strip() for ln in out.splitlines() if ln.strip() and
                not ln.startswith(("INFO", "WARNING", "ERROR"))]
    except Exception:  # noqa: BLE001
        return []


def create_avd(name: str, image: str, memory_mb: int = 2048, cores: int = 2,
               width: int = 1080, height: int = 2340, density: int = 440) -> dict:
    """创建 AVD 并写 config.ini 定制硬件参数。"""
    avdm = _find_tool(None, "cmdline-tools/latest/bin/avdmanager.bat")
    if not avdm:
        raise RuntimeError("avdmanager 不可用，请先执行一键引导")
    if not (name and RE_AVD_NAME.match(name)):
        raise ValueError("AVD 名称仅允许字母/数字/下划线/连字符（≤64 位）")
    if not image.startswith("system-images;") or not RE_SDK_PKG.match(image):
        raise ValueError(f"非法镜像标识: {image}")
    if not (256 <= memory_mb <= 16384):
        raise ValueError("内存须在 256~16384 MB 之间")
    if not (1 <= cores <= 16):
        raise ValueError("CPU 核心数须在 1~16 之间")

    code, out = _run_bat(avdm, ["create", "avd", "-n", name, "-k", image,
                                "-d", "pixel_4"], timeout=300)
    # avdmanager 对已存在 AVD 返回非 0
    if code != 0 and "already exists" not in out.lower():
        raise RuntimeError(f"创建 AVD 失败: {out[-500:]}")

    config_path = _avd_config_path(name)
    if config_path is not None and config_path.is_file():
        lines = config_path.read_text(encoding="utf-8", errors="replace").splitlines()
        overrides = {
            "hw.ramSize": str(memory_mb),
            "hw.cpu.ncore": str(cores),
            "hw.lcd.width": str(width),
            "hw.lcd.height": str(height),
            "hw.lcd.density": str(density),
            "hw.keyboard": "yes",
        }
        kept, seen = [], set()
        for ln in lines:
            key = ln.split("=", 1)[0].strip()
            if key in overrides:
                kept.append(f"{key}={overrides[key]}")
                seen.add(key)
            else:
                kept.append(ln)
        for k, v in overrides.items():
            if k not in seen:
                kept.append(f"{k}={v}")
        config_path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return {"name": name, "image": image, "memory_mb": memory_mb, "cores": cores,
            "resolution": f"{width}x{height}@{density}dpi"}


def _avd_config_path(name: str) -> Path | None:
    home = Path.home() / ".android" / "avd" / f"{name}.avd" / "config.ini"
    return home if home.is_file() else None


def delete_avd(name: str) -> dict:
    if not RE_AVD_NAME.match(name):
        raise ValueError("非法 AVD 名称")
    running = _procs.get(name)
    if running and running.poll() is None:
        raise RuntimeError(f"AVD {name} 正在运行，请先停止")
    avdm = _find_tool(None, "cmdline-tools/latest/bin/avdmanager.bat")
    if not avdm:
        raise RuntimeError("avdmanager 不可用")
    code, out = _run_bat(avdm, ["delete", "avd", "-n", name], timeout=60)
    if code != 0:
        raise RuntimeError(f"删除 AVD 失败: {out[-300:]}")
    return {"deleted": name}


# ===== AVD 启停 =====

_procs: dict[str, dict] = {}   # name -> {proc, port}
_procs_lock = threading.Lock()
_BASE_PORT = 5554              # 模拟器 console 端口（serial = emulator-<port>）
_MAX_INSTANCES = 8


def _alloc_port() -> int:
    used = {v["port"] for v in _procs.values()}
    for i in range(_MAX_INSTANCES):
        p = _BASE_PORT + i * 2
        if p not in used:
            return p
    raise RuntimeError("运行中模拟器实例已达上限（8 个）")


def start_avd(name: str, *, headless: bool = False, proxy_port: int = 0,
              memory_mb: int | None = None, cores: int | None = None,
              install_cert: bool = True) -> dict:
    """启动 AVD；proxy_port>0 时挂 mitmproxy 抓包代理，install_cert 时自动装系统证书。"""
    if not RE_AVD_NAME.match(name):
        raise ValueError("非法 AVD 名称")
    emu = _find_tool(None, "emulator/emulator.exe")
    if not emu:
        raise RuntimeError("emulator 不可用，请先执行一键引导")
    with _procs_lock:
        old = _procs.get(name)
        if old is not None and old["proc"].poll() is None:
            raise RuntimeError(f"AVD {name} 已在运行")
        port = _alloc_port()

    args = [str(emu), "-avd", name, "-port", str(port), "-no-snapshot-load"]
    if headless:
        args.append("-no-window")
    if memory_mb:
        args += ["-memory", str(memory_mb)]
    if cores:
        args += ["-cores", str(cores)]
    if proxy_port:
        args += ["-http-proxy", f"http://127.0.0.1:{proxy_port}",
                 "-writable-system"]

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=creationflags)
    with _procs_lock:
        _procs[name] = {"proc": proc, "port": port}

    if install_cert and proxy_port:
        threading.Thread(target=_wait_and_install_cert, args=(name, port),
                         daemon=True, name=f"android-cert-{name}").start()
    return {"name": name, "pid": proc.pid, "port": port,
            "serial": f"emulator-{port}", "proxy_port": proxy_port,
            "headless": headless,
            "note": "启动中（首次冷启动约 1~2 分钟）；证书将自动安装"}


def _wait_and_install_cert(name: str, port: int, max_wait: int = 300) -> None:
    """等待模拟器 boot 完成，然后 root + 装 mitmproxy CA 到系统证书目录。"""
    adb = _find_tool(None, "platform-tools/adb.exe")
    if not adb:
        return
    serial = f"emulator-{port}"
    for _ in range(max_wait // 5):
        time.sleep(5)
        with _procs_lock:
            rec = _procs.get(name)
            if rec is None or rec["proc"].poll() is not None:
                return
        try:
            code, out = _run_exe(adb, ["-s", serial, "shell", "getprop",
                                       "sys.boot_completed"], timeout=30)
            if code == 0 and out.strip().startswith("1"):
                break
        except Exception:  # noqa: BLE001
            continue
    try:
        _install_mitm_cert(adb, serial)
    except Exception:  # noqa: BLE001
        pass  # 证书失败不阻塞模拟器使用（用户证书路径仍可用，仅 Android7+ 应用不信任）


def _calc_subject_hash_old(cert_pem: bytes) -> str:
    """OpenSSL subject_hash_old 等价实现：MD5(subject DER) 前 4 字节小写十六进制。"""
    from cryptography import x509

    cert = x509.load_pem_x509_certificate(cert_pem)
    der = cert.subject.public_bytes()
    digest = hashlib.md5(der).digest()
    return (digest[0] | digest[1] << 8 | digest[2] << 16 | digest[3] << 24) \
        .to_bytes(4, "little").hex()


def _install_mitm_cert(adb: Path, serial: str) -> dict:
    """把 mitmproxy CA 装为 Android 系统证书（需 google_apis 镜像可 root）。"""
    if not MITMPROXY_CERT.is_file():
        return {"installed": False,
                "reason": f"未找到 {MITMPROXY_CERT}（先在攻击探测页启动一次抓包即可生成）"}
    pem = MITMPROXY_CERT.read_bytes()
    try:
        hash_name = _calc_subject_hash_old(pem)
    except Exception as e:  # noqa: BLE001
        return {"installed": False, "reason": f"证书解析失败: {e}"}
    remote_name = f"{hash_name}.0"
    tmp = Path(os.environ.get("TEMP", ".")) / remote_name
    tmp.write_bytes(pem)
    steps = [
        ["root"],
        ["wait-for-device"],
        ["remount"],
        ["push", str(tmp), f"/system/etc/security/cacerts/{remote_name}"],
        ["shell", "chmod", "644", f"/system/etc/security/cacerts/{remote_name}"],
    ]
    results = []
    for s in steps:
        try:
            code, out = _run_exe(adb, ["-s", serial, *s], timeout=120)
            results.append({"cmd": " ".join(s), "code": code,
                            "out": out[-200:] if out else ""})
        except Exception as e:  # noqa: BLE001
            results.append({"cmd": " ".join(s), "code": -1, "out": str(e)})
    ok = any(r["cmd"] == "push" and r["code"] == 0 for r in results)
    return {"installed": ok, "cert_name": remote_name, "steps": results}


def stop_avd(name: str) -> dict:
    with _procs_lock:
        rec = _procs.get(name)
    if rec is None or rec["proc"].poll() is not None:
        if rec is not None:
            with _procs_lock:
                _procs.pop(name, None)
        return {"stopped": name, "note": "未由本服务启动或已退出"}
    adb = _find_tool(None, "platform-tools/adb.exe")
    if adb:
        try:
            _run_exe(adb, ["-s", f"emulator-{rec['port']}", "emu", "kill"],
                     timeout=15)
        except Exception:  # noqa: BLE001
            pass
    proc = rec["proc"]
    try:
        proc.terminate()
        proc.wait(timeout=10)
    except Exception:  # noqa: BLE001
        proc.kill()
    with _procs_lock:
        _procs.pop(name, None)
    return {"stopped": name}


def is_running(name: str) -> bool:
    with _procs_lock:
        rec = _procs.get(name)
    return rec is not None and rec["proc"].poll() is None


# ===== adb / APP 管理 =====

def adb_devices() -> list[dict]:
    adb = _find_tool(None, "platform-tools/adb.exe")
    if not adb:
        raise RuntimeError("adb 不可用，请先执行一键引导")
    code, out = _run_exe(adb, ["devices", "-l"], timeout=30)
    if code != 0:
        raise RuntimeError(f"adb devices 失败: {out[-300:]}")
    devices = []
    for ln in out.splitlines()[1:]:
        if not ln.strip():
            continue
        parts = ln.split()
        entry = {"serial": parts[0], "state": parts[1] if len(parts) > 1 else "?",
                 "model": "", "product": ""}
        for p in parts[2:]:
            if p.startswith("model:"):
                entry["model"] = p.split(":", 1)[1]
            if p.startswith("product:"):
                entry["product"] = p.split(":", 1)[1]
        devices.append(entry)
    return devices


def install_apk(serial: str, apk_path: str) -> dict:
    adb = _find_tool(None, "platform-tools/adb.exe")
    if not adb:
        raise RuntimeError("adb 不可用")
    if not apk_path.lower().endswith(".apk"):
        raise ValueError("仅支持 .apk 文件")
    p = Path(apk_path)
    if not p.is_file():
        raise FileNotFoundError(apk_path)
    code, out = _run_exe(adb, ["-s", serial, "install", "-r", "-t", str(p)],
                         timeout=600)
    if code != 0 or "Success" not in out:
        raise RuntimeError(f"APK 安装失败: {out[-400:]}")
    return {"installed": True, "serial": serial, "apk": p.name}


def launch_app(serial: str, package: str, activity: str = "") -> dict:
    # 包名/Activity 白名单：adb shell 会把参数拼接交给设备端 sh 执行，
    # 含 ; $() 等元字符的包名可在设备 shell 内注入命令
    if not RE_ADB_PKG.match(package):
        raise ValueError("非法包名")
    if activity and not RE_ACTIVITY.match(activity):
        raise ValueError("非法 Activity 名")
    adb = _find_tool(None, "platform-tools/adb.exe")
    if not adb:
        raise RuntimeError("adb 不可用")
    if activity:
        comp = f"{package}/{activity}"
    else:
        # monkey 方式启动默认入口 Activity（无需知道 activity 名）
        code, out = _run_exe(adb, ["-s", serial, "shell",
                                   "monkey", "-p", package,
                                   "-c", "android.intent.category.LAUNCHER", "1"],
                             timeout=60)
        if code != 0:
            raise RuntimeError(f"启动失败: {out[-300:]}")
        return {"launched": True, "package": package}
    code, out = _run_exe(adb, ["-s", serial, "shell", "am", "start", "-n", comp],
                         timeout=60)
    if code != 0:
        raise RuntimeError(f"启动失败: {out[-300:]}")
    return {"launched": True, "component": comp}


def uninstall_app(serial: str, package: str) -> dict:
    # 包名白名单校验
    if not RE_ADB_PKG.match(package):
        raise ValueError("非法包名")
    adb = _find_tool(None, "platform-tools/adb.exe")
    if not adb:
        raise RuntimeError("adb 不可用")
    code, out = _run_exe(adb, ["-s", serial, "uninstall", package], timeout=120)
    return {"uninstalled": code == 0, "package": package, "out": out[-200:]}


def list_packages(serial: str, third_party: bool = True) -> list[str]:
    adb = _find_tool(None, "platform-tools/adb.exe")
    if not adb:
        raise RuntimeError("adb 不可用")
    args = ["-s", serial, "shell", "pm", "list",
            "packages" + ("", " -3")[third_party]]
    code, out = _run_exe(adb, args, timeout=60)
    if code != 0:
        raise RuntimeError(f"列包失败: {out[-300:]}")
    return [ln.replace("package:", "").strip()
            for ln in out.splitlines() if ln.startswith("package:")]
