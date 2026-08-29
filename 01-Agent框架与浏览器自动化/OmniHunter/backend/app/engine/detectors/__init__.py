"""检测插件自动发现与加载 —— 每个漏洞一个插件文件，格式统一。"""
from __future__ import annotations

import importlib
import pkgutil

from ..base import DetectorPlugin


def load_plugins() -> list[DetectorPlugin]:
    """扫描本包内所有插件模块，实例化 DetectorPlugin 子类。"""
    plugins: list[DetectorPlugin] = []
    seen_ids: set[str] = set()
    for mod_info in pkgutil.iter_modules(__path__):
        if mod_info.name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f".{mod_info.name}", __name__)
        except Exception as e:  # noqa: BLE001 —— 单插件加载失败不拖垮引擎
            print(f"[engine] 插件加载失败 {mod_info.name}: {e}", flush=True)
            continue
        for attr in vars(mod).values():
            if (isinstance(attr, type) and issubclass(attr, DetectorPlugin)
                    and attr is not DetectorPlugin
                    and getattr(attr, "id", "")):
                inst = attr()
                if inst.id not in seen_ids:
                    seen_ids.add(inst.id)
                    plugins.append(inst)
    return plugins
