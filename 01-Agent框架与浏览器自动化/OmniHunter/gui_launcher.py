"""aififteen Hunter · 图形化启动壳（桌面控制面板）。

纯标准库实现：Tkinter 做窗口 + 进程管理 + 系统默认浏览器打开 Web UI。
零额外依赖：无需 PyQt / webview / Electron，用户只需安装 Python 3.10+ 即可双击使用。

操作模式：
- 点击「启动服务」 → 自动起后端 uvicorn（18800），开发模式下同时起前端 dev（5173）
- 点击「打开界面」 → 用系统默认浏览器访问 Web 控制台
- 点击「停止服务」 → 杀后端 + 前端进程
- 运行日志实时滚动显示在下方文本框

用法：
    python gui_launcher.py [dev|prod]
    # 不带参数：开发模式（后端 18800 + 前端 5173）
    # prod 模式：需前端已构建（frontend/dist 存在），仅起后端并托管 UI
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

HERE = Path(__file__).resolve().parent
BACKEND_DIR = HERE / "backend"
FRONTEND_DIR = HERE / "frontend"

DEV_URL = "http://localhost:5173"
PROD_URL = "http://localhost:18800"
BACKEND_URL = "http://localhost:18800"


class HunterLauncher:
    def __init__(self, mode: str = "dev"):
        self.mode = "prod" if mode.lower() == "prod" else "dev"
        self.backend_proc: subprocess.Popen | None = None
        self.frontend_proc: subprocess.Popen | None = None
        self.log_lock = threading.Lock()

        # ---- Tk 根窗口 ----
        self.root = tk.Tk()
        self.root.title(f"aififteen Hunter · 桌面启动壳 ({self.mode})")
        self.root.geometry("760x520")
        self.root.minsize(640, 440)
        self._style()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---- 样式 ----
    def _style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:  # noqa: BLE001
            pass
        bg = "#161a23"
        fg = "#e5e7eb"
        self.root.configure(bg=bg)
        style.configure(".", background=bg, foreground=fg, fieldbackground="#1f2430",
                        bordercolor="#2a2f3e", lightcolor="#2a2f3e", darkcolor="#101319")
        style.configure("TButton", padding=(14, 8), font=("Segoe UI", 10))
        style.map("TButton",
                  background=[("!disabled", "#2f6fe8"), ("active", "#4b86f2"), ("disabled", "#3a3f52")],
                  foreground=[("!disabled", "#ffffff")])
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#9cc2ff")
        style.configure("Sub.TLabel", foreground="#9ca3af", font=("Segoe UI", 9))
        style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"))
        style.configure("Good.Status.TLabel", foreground="#10b981")
        style.configure("Warn.Status.TLabel", foreground="#f59e0b")

    # ---- UI 构造 ----
    def _build_ui(self):
        pad = {"padx": 16, "pady": 10}
        top = ttk.Frame(self.root)
        top.pack(fill="x", **pad)
        title = ttk.Label(top, text="🛡  aififteen Hunter", style="Header.TLabel")
        title.pack(side="left")
        self.status_var = tk.StringVar(value="未启动")
        status = ttk.Label(top, textvariable=self.status_var, style="Warn.Status.TLabel")
        status.pack(side="right")

        sub = ttk.Label(
            self.root,
            text=f"模式：{'开发（后端 18800 + 前端 5173）' if self.mode == 'dev' else '生产（仅后端 18800，托管构建产物）'}",
            style="Sub.TLabel",
        )
        sub.pack(fill="x", padx=16)

        # 按钮栏
        bar = ttk.Frame(self.root)
        bar.pack(fill="x", **pad)
        self.btn_start = ttk.Button(bar, text="▶ 启动服务", command=self.start_services)
        self.btn_start.pack(side="left", padx=(0, 10))
        self.btn_open = ttk.Button(bar, text="🌐 打开界面", command=self.open_browser, state="disabled")
        self.btn_open.pack(side="left", padx=(0, 10))
        self.btn_stop = ttk.Button(bar, text="■ 停止服务", command=self.stop_services, state="disabled")
        self.btn_stop.pack(side="left", padx=(0, 10))
        ttk.Button(bar, text="打开数据目录", command=self.open_data_dir).pack(side="left")

        # 地址栏（可点击的 Label）
        info = ttk.Frame(self.root)
        info.pack(fill="x", padx=16, pady=(4, 8))
        addr_text = f"界面地址：{DEV_URL if self.mode == 'dev' else PROD_URL}  ·  后端 API：{BACKEND_URL}/docs"
        link = ttk.Label(info, text=addr_text + "  （点击访问）", style="Sub.TLabel", cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda _e: self.open_browser())

        # 日志区
        ttk.Label(self.root, text="运行日志：", style="Sub.TLabel").pack(anchor="w", padx=16, pady=(4, 2))
        self.log = scrolledtext.ScrolledText(
            self.root, height=18, wrap="none", font=("Consolas", 9),
            bg="#0f1218", fg="#cbd5e1", insertbackground="#cbd5e1", relief="flat",
        )
        self.log.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        self.log.configure(state="disabled")
        self._log(
            "欢迎使用 aififteen Hunter 桌面启动壳。\n"
            "点击「启动服务」后会自动初始化后端依赖（首次较久），然后一键打开界面。\n"
            "关闭此窗口会自动停止所有后台进程。\n"
        )

    # ---- 日志 ----
    def _log(self, msg: str):
        with self.log_lock:
            self.log.configure(state="normal")
            self.log.insert("end", msg.rstrip() + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")

    def _pump_log(self, stream, tag: str, proc: subprocess.Popen):
        """后台线程把子进程 stdout/stderr 逐行写进日志区。"""
        try:
            for line in stream:
                if proc.poll() is not None:
                    break
                try:
                    text = line.decode("utf-8", "replace").rstrip()
                except Exception:  # noqa: BLE001
                    continue
                if text:
                    self.root.after(0, self._log, f"[{tag}] {text}")
        except Exception as e:  # noqa: BLE001
            self.root.after(0, self._log, f"[{tag}] pump error: {e}")

    # ---- 状态 ----
    def _set_status(self, state: str, label: str):
        style_map = {"running": "Good.Status.TLabel", "stopped": "Warn.Status.TLabel"}
        style = ttk.Label(self.root)
        self.status_label.configure(style=style_map.get(state, ""))  # type: ignore[attr-defined]
        # 上面那行只是占位取 style，真正通过 status_var 与 configure 设置
        self.status_var.set(label)
        status_child = [c for c in self.root.winfo_children()
                        if isinstance(c, ttk.Frame) and len(c.winfo_children()) >= 2]
        if status_child:
            for c in status_child[0].winfo_children():
                if isinstance(c, ttk.Label) and c["textvariable"] == str(self.status_var):
                    c.configure(style=style_map.get(state, "Status.TLabel"))
                    break

    def _set_running(self, running: bool):
        self.btn_start.configure(state=("disabled" if running else "normal"))
        self.btn_stop.configure(state=("normal" if running else "disabled"))
        self.btn_open.configure(state=("normal" if running else "disabled"))
        if running:
            self.status_var.set("运行中")
            for c in self.root.winfo_children():
                if isinstance(c, ttk.Frame):
                    for cc in c.winfo_children():
                        if isinstance(cc, ttk.Label) and cc["textvariable"] == str(self.status_var):
                            cc.configure(style="Good.Status.TLabel")
        else:
            self.status_var.set("已停止")
            for c in self.root.winfo_children():
                if isinstance(c, ttk.Frame):
                    for cc in c.winfo_children():
                        if isinstance(cc, ttk.Label) and cc["textvariable"] == str(self.status_var):
                            cc.configure(style="Warn.Status.TLabel")

    # ---- 启动/停止 ----
    def start_services(self):
        if self.backend_proc and self.backend_proc.poll() is None:
            messagebox.showinfo("提示", "服务已在运行")
            return
        self._log("--- 启动服务 ---")
        # 1. 后端
        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = (
                str(BACKEND_DIR / "vendor") + os.pathsep
                + (env.get("PYTHONPATH") or "")
            )
            if (BACKEND_DIR / "vendor" / "httpx").is_dir():
                python = sys.executable
            else:
                python = sys.executable
                self._log("backend/vendor 未就绪，首次启动会自动安装依赖（请耐心等待）。")
            uvicorn_args = ["app.main:app", "--host", "0.0.0.0", "--port", "18800"]
            if self.mode == "dev":
                uvicorn_args.insert(0, "--reload")
            cmd = [python, "-m", "uvicorn", *uvicorn_args]
            popen_kwargs = dict(
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                cwd=str(BACKEND_DIR), env=env,
            )
            if os.name == "nt":
                popen_kwargs["creationflags"] = (subprocess.DETACHED_PROCESS |
                                                 subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                popen_kwargs["start_new_session"] = True
            self.backend_proc = subprocess.Popen(cmd, **popen_kwargs)
            threading.Thread(target=self._pump_log,
                             args=(self.backend_proc.stdout, "BE", self.backend_proc),
                             daemon=True).start()
            self._log(f"后端已启动（pid={self.backend_proc.pid}）")
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("启动失败", f"后端启动失败：{e}")
            self._log(f"[ERR] 后端启动：{e}")
            return

        # 2. 前端（dev 模式）
        if self.mode == "dev":
            try:
                node_cmd = ["npm", "run", "dev"] if os.name == "nt" else ["npm", "run", "dev"]
                fe_kwargs = dict(
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    cwd=str(FRONTEND_DIR), env=os.environ.copy(),
                    shell=(os.name != "nt"),
                )
                if os.name == "nt":
                    fe_kwargs["creationflags"] = (subprocess.DETACHED_PROCESS |
                                                   subprocess.CREATE_NEW_PROCESS_GROUP)
                else:
                    fe_kwargs["start_new_session"] = True
                self.frontend_proc = subprocess.Popen(node_cmd, **fe_kwargs)
                threading.Thread(target=self._pump_log,
                                 args=(self.frontend_proc.stdout, "FE", self.frontend_proc),
                                 daemon=True).start()
                self._log(f"前端已启动（pid={self.frontend_proc.pid}），首次启动较慢 WAIT。")
            except Exception as e:  # noqa: BLE001
                messagebox.showwarning("前端启动失败",
                                       f"后端已启，可直接访问 {BACKEND_URL}。前端错误：{e}")
                self._log(f"[WARN] 前端：{e}")

        self._set_running(True)

    def stop_services(self):
        self._log("--- 停止服务 ---")
        stopped = 0
        for name, proc in (("前端", self.frontend_proc), ("后端", self.backend_proc)):
            if proc is None or proc.poll() is not None:
                continue
            try:
                if os.name == "nt":
                    # Windows：向进程组发 Ctrl-Break
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                else:
                    # POSIX：向整个进程组发 SIGTERM，然后 SIGKILL
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    try:
                        proc.wait(timeout=6)
                    except subprocess.TimeoutExpired:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                stopped += 1
                self._log(f"{name} 已停止（pid={proc.pid}）")
            except Exception as e:  # noqa: BLE001
                self._log(f"[WARN] 停止 {name}：{e}")
        self.frontend_proc = None
        self.backend_proc = None
        self._set_running(False)
        messagebox.showinfo("停止", f"服务已停止（共 {stopped} 个进程）。")

    def open_browser(self):
        url = DEV_URL if self.mode == "dev" else PROD_URL
        webbrowser.open(url, new=2)

    def open_data_dir(self):
        data_dir = BACKEND_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(str(data_dir))  # type: ignore[attr-defined]
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", str(data_dir)])
            else:
                subprocess.Popen(["xdg-open", str(data_dir)])
        except Exception as e:  # noqa: BLE001
            messagebox.showinfo("数据目录", str(data_dir) + f"\n（打开失败：{e}）")

    def on_close(self):
        any_alive = any(p and p.poll() is None for p in (self.backend_proc, self.frontend_proc))
        if any_alive and not messagebox.askokcancel("退出", "服务仍在运行，退出时会一并停止。确定退出？"):
            return
        try:
            self.stop_services()
        except Exception:  # noqa: BLE001
            pass
        self.root.destroy()

    def run(self):
        self._set_running(False)
        self.root.mainloop()


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "dev"
    HunterLauncher(mode).run()


if __name__ == "__main__":
    main()
