"""settings_check — ~/.claude/settings.json 健康度。

检查项：
  1. 文件是否存在
  2. JSON 是否合法
  3. permissions.allow 数量 + 是否含通配符
"""
from __future__ import annotations

import json

from ..locator import settings_json
from ..types import CheckResult, CheckStatus


def check() -> list[CheckResult]:
    """settings_check 主入口。"""
    path = settings_json()
    results: list[CheckResult] = []

    # 1) 文件存在性
    if not path.exists():
        results.append(CheckResult(
            CheckStatus.WARN,
            "settings.exists",
            f"文件不存在: {path}",
        ))
        return results

    # 2) JSON 合法性
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        results.append(CheckResult(
            CheckStatus.FAIL,
            "settings.json_valid",
            f"JSON 解析失败: {e}",
        ))
        return results

    if not isinstance(data, dict):
        results.append(CheckResult(
            CheckStatus.FAIL,
            "settings.json_valid",
            f"顶层不是 dict: {type(data).__name__}",
        ))
        return results

    results.append(CheckResult(
        CheckStatus.PASS,
        "settings.json_valid",
        f"JSON 合法（{len(data)} 个顶层键）",
        {"top_level_keys": sorted(data.keys())},
    ))

    # 3) permissions.allow 检查
    perms = data.get("permissions", {})
    if not isinstance(perms, dict):
        results.append(CheckResult(
            CheckStatus.WARN,
            "settings.permissions",
            f"permissions 字段不是 dict: {type(perms).__name__}",
        ))
    else:
        allow = perms.get("allow", [])
        deny = perms.get("deny", [])
        if not isinstance(allow, list):
            allow = []
        if not isinstance(deny, list):
            deny = []

        # 检测冲突：同一规则在 allow 和 deny 都出现
        allow_set = set(allow)
        deny_set = set(deny)
        conflicts = sorted(allow_set & deny_set)

        # 检测通配符
        wildcards = [r for r in allow if "*" in r]

        if conflicts:
            results.append(CheckResult(
                CheckStatus.FAIL,
                "settings.permissions.conflict",
                f"allow 和 deny 冲突 {len(conflicts)} 条: {conflicts[:3]}{'...' if len(conflicts) > 3 else ''}",
                {"conflicts": conflicts},
            ))

        if not allow:
            results.append(CheckResult(
                CheckStatus.WARN,
                "settings.permissions.allow",
                "为空（所有工具需手动确认）",
            ))
        else:
            if wildcards:
                results.append(CheckResult(
                    CheckStatus.WARN,
                    "settings.permissions.allow",
                    f"{len(allow)} 条规则（含通配符 {len(wildcards)} 条: {wildcards}）",
                    {"count": len(allow), "wildcards": wildcards},
                ))
            else:
                results.append(CheckResult(
                    CheckStatus.PASS,
                    "settings.permissions.allow",
                    f"{len(allow)} 条规则（无通配符）",
                    {"count": len(allow)},
                ))

    return results