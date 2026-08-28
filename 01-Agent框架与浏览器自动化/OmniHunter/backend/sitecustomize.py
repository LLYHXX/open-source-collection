"""Python 启动时自动加载：把 vendor 目录加入 sys.path。

后端依赖装到 backend/vendor（避免污染系统/被沙箱拦截）。
本文件放在 backend/ 目录，Python 启动会自动 import sitecustomize，
使 `import fastapi/openai/...` 等可解析，消除 IDE 红点。
"""
import os
import sys

_VENDOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if os.path.isdir(_VENDOR) and _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)
