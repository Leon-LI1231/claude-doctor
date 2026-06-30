"""env_check — 环境变量一致性体检。

对比三处 ANTHROPIC_*：
  1. process env (os.environ) — 进程实际看到的
  2. settings.json env 块    — Claude Code 配置文件
  3. Windows 注册表 HKCU\\Environment — 用户级环境变量

输出多条 CheckResult（每个变量 × 最多 3 条比对）。
对 TOKEN/KEY 类敏感字段自动 mask。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from ..locator import settings_json
from ..types import CheckResult, CheckStatus

# 必须检测的 ANTHROPIC_* 变量
ANTHROPIC_VARS = [
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
]


def _mask(value: str, var_name: str) -> str:
    """对敏感字段（TOKEN/KEY）做 mask 处理。"""
    upper = var_name.upper()
    if "TOKEN" in upper or "KEY" in upper or "SECRET" in upper:
        if len(value) <= 10:
            return "***"
        return value[:8] + "***"
    return value


def _read_registry_env() -> dict[str, str]:
    """读 HKCU\\Environment 的用户级环境变量（仅 Windows）。

    非 Windows 平台 / 读取失败 → 返回空 dict（不影响其他检查）。
    """
    if sys.platform != "win32":
        return {}
    try:
        import winreg
    except ImportError:
        return {}

    result: dict[str, str] = {}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    result[name] = value
                except OSError:
                    break
                i += 1
    except OSError:
        pass
    return result


def _read_settings_env() -> dict[str, str]:
    """读 ~/.claude/settings.json 的 env 块。

    文件不存在 / JSON 不合法 / env 字段缺失 → 返回空 dict。
    """
    path = settings_json()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        env = data.get("env", {})
        return env if isinstance(env, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def check() -> list[CheckResult]:
    """env_check 主入口。返回 0~多条 CheckResult。"""
    results: list[CheckResult] = []
    proc_env = dict(os.environ)  # 快照，避免 check 过程中变化
    reg_env = _read_registry_env()
    set_env = _read_settings_env()

    for var in ANTHROPIC_VARS:
        proc_val = proc_env.get(var)
        reg_val = reg_env.get(var)
        set_val = set_env.get(var)

        # 1) process env 是否有值
        if proc_val:
            results.append(CheckResult(
                CheckStatus.PASS,
                f"env.process.{var}",
                f"已设置: {_mask(proc_val, var)}",
                {"source": "process"},
            ))
        else:
            results.append(CheckResult(
                CheckStatus.WARN,
                f"env.process.{var}",
                "未设置（当前进程无此变量）",
            ))

        # 2) settings.json vs process 的一致性
        if set_val is not None and set_val != proc_val:
            results.append(CheckResult(
                CheckStatus.WARN,
                f"env.settings_vs_process.{var}",
                f"settings.json={_mask(set_val, var)!r} ≠ process={_mask(proc_val or '', var)!r}",
                {"settings": set_val, "process": proc_val},
            ))

        # 3) registry vs process 的一致性
        if reg_val is not None and reg_val != proc_val:
            results.append(CheckResult(
                CheckStatus.WARN,
                f"env.registry_vs_process.{var}",
                f"registry={_mask(reg_val, var)!r} ≠ process={_mask(proc_val or '', var)!r}",
                {"registry": reg_val, "process": proc_val},
            ))

    return results