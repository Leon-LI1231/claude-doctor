"""claude_doctor.core.checks — 各 check 模块的注册表。

新增 check 只需：(1) 在本目录加一个 check_X.py，(2) 在 CHECK_REGISTRY 注册。
"""
from __future__ import annotations

from . import env_check, mcp_check, settings_check

CHECK_REGISTRY: dict[str, "object"] = {  # type: ignore[name-defined]
    # 注意：保留稳定顺序，给报告输出可预测性
    "env": env_check,
    "settings": settings_check,
    "mcp": mcp_check,
}


__all__ = ["CHECK_REGISTRY", "env_check", "settings_check", "mcp_check"]