"""settings_check — ~/.claude/settings.json 健康度 + 项目级 settings 冲突检测。

检查项：
  1. 用户级文件是否存在 + JSON 合法
  2. permissions.allow 数量 + 通配符 + allow/deny 冲突
  3. (v1.0 新增) 项目级 settings.json vs settings.local.json 冲突检测

v1.0 冲突检测规则：
  - 字符串冲突（model / effortLevel / outputStyle）:  WARN
  - 数组"被替换"风险（permissions.allow 数量减少）:    WARN
  - 安全策略绕过风险（permissions.deny 数量减少）:     FAIL
"""
from __future__ import annotations

import json
from pathlib import Path

from ..locator import find_project_settings, settings_json
from ..types import CheckResult, CheckStatus


# ============================================================
# 用户级 settings 检查（v0.1.0 原有逻辑）
# ============================================================

def _load_layer(path: Path) -> tuple[dict | None, bool]:
    """加载一个 settings 文件。

    Args:
        path: settings 文件路径。

    Returns:
        (data, exists) 二元组。
        - 文件不存在: (None, False)
        - JSON 不合法: (None, True)（exists=True 但 data=None，caller 应判 FAIL）
        - 顶层不是 dict: ({}, True)（data={} 表示"存在但空"）
        - 正常: (data, True)
    """
    if not path.exists():
        return (None, False)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return (None, True)
    if not isinstance(data, dict):
        return ({}, True)
    return (data, True)


def _check_user_settings() -> list[CheckResult]:
    """检查用户级 ~/.claude/settings.json（v0.1.0 逻辑保留）。"""
    path = settings_json()
    results: list[CheckResult] = []

    if not path.exists():
        results.append(CheckResult(
            CheckStatus.WARN,
            "settings.exists",
            f"文件不存在: {path}",
        ))
        return results

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

    # permissions 检查
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

        # allow 和 deny 内部冲突
        allow_set = set(allow)
        deny_set = set(deny)
        conflicts = sorted(allow_set & deny_set)

        # 通配符
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


# ============================================================
# v1.0 新增：项目级 settings 冲突检测
# ============================================================

# 需要检测冲突的字符串字段
_STRING_FIELDS = ("model", "effortLevel", "outputStyle")


def _detect_string_conflicts(
    project_data: dict,
    local_data: dict,
) -> list[CheckResult]:
    """检测字符串字段冲突（model / effortLevel / outputStyle）。"""
    results: list[CheckResult] = []
    for field in _STRING_FIELDS:
        p_val = project_data.get(field)
        l_val = local_data.get(field)
        # 两边都设置但值不同 → 冲突
        if p_val is not None and l_val is not None and p_val != l_val:
            effective = l_val  # local 覆盖
            results.append(CheckResult(
                CheckStatus.WARN,
                f"settings.conflict.{field}",
                (
                    f"字符串覆盖冲突: project={p_val!r}, local={l_val!r}, "
                    f"实际生效={effective!r} (local 覆盖)"
                ),
                {
                    "type": "string_override",
                    "field": field,
                    "project": p_val,
                    "local": l_val,
                    "effective": effective,
                    "source": "local",
                },
            ))
    return results


def _detect_array_conflict(
    project_data: dict,
    local_data: dict,
    array_key: str,
    severity: CheckStatus,
    risk_desc: str,
) -> CheckResult | None:
    """检测 permissions.{array_key} 数组"被替换"风险。

    规则:
      - 如果 project 有 N 条, local 有 M 条, M < N → 整段替换风险
      - 提示"丢了 N-M 条" + 严重度由 caller 决定 (WARN/FAIL)

    Returns:
        None（无冲突）或 CheckResult。
    """
    p_perms = project_data.get("permissions", {})
    l_perms = local_data.get("permissions", {})
    p_arr = p_perms.get(array_key, [])
    l_arr = l_perms.get(array_key, [])

    # 类型检查（防御性）
    if not isinstance(p_arr, list) or not isinstance(l_arr, list):
        return None

    # 数量比较
    p_n = len(p_arr)
    l_n = len(l_arr)

    # 仅当 project 有 N 条、local 显式设置（哪怕是空数组）且数量更少时才报警
    if p_n > 0 and l_n < p_n:
        missing_n = p_n - l_n
        return CheckResult(
            severity,
            f"settings.conflict.permissions.{array_key}",
            (
                f"{risk_desc}: project 有 {p_n} 条, local 有 {l_n} 条 "
                f"(整段替换风险, 丢了 {missing_n} 条)"
            ),
            {
                "type": "array_shrink",
                "field": f"permissions.{array_key}",
                "project_count": p_n,
                "local_count": l_n,
                "missing_count": missing_n,
                "project_rules": p_arr,
                "local_rules": l_arr,
            },
        )
    return None


def _check_project_conflicts() -> list[CheckResult]:
    """检查项目级 settings 冲突（v1.0 新增）。

    对比：
      - .claude/settings.json       (项目级 / 团队约定)
      - .claude/settings.local.json (项目级 / 个人覆盖)
    """
    results: list[CheckResult] = []
    project_path, local_path = find_project_settings()

    # 加载两层
    project_data, project_exists = _load_layer(project_path)
    local_data, local_exists = _load_layer(local_path)

    # 如果两个文件都不存在 → 不跑冲突检测（合法状态）
    if not project_exists and not local_exists:
        return results

    # 文件存在但 JSON 不合法
    if project_exists and project_data is None:
        results.append(CheckResult(
            CheckStatus.FAIL,
            "settings.conflict.project_json_valid",
            f"项目级 settings.json JSON 解析失败: {project_path}",
        ))
        return results  # 无法继续对比
    if local_exists and local_data is None:
        results.append(CheckResult(
            CheckStatus.FAIL,
            "settings.conflict.local_json_valid",
            f"项目级 settings.local.json JSON 解析失败: {local_path}",
        ))
        return results

    # 报告检测范围
    layers = []
    if project_exists:
        layers.append(f"project: {project_path}")
    if local_exists:
        layers.append(f"local: {local_path}")
    results.append(CheckResult(
        CheckStatus.PASS,
        "settings.conflict.scanned",
        f"扫描 {len(layers)} 层: {' / '.join(layers)}",
        {"project_exists": project_exists, "local_exists": local_exists},
    ))

    # 字符串字段冲突
    if project_exists and local_exists:
        results.extend(_detect_string_conflicts(project_data, local_data))

        # 数组"被替换"风险
        allow_conflict = _detect_array_conflict(
            project_data, local_data,
            array_key="allow",
            severity=CheckStatus.WARN,
            risk_desc="权限 allow 收紧",
        )
        if allow_conflict:
            results.append(allow_conflict)

        deny_conflict = _detect_array_conflict(
            project_data, local_data,
            array_key="deny",
            severity=CheckStatus.FAIL,
            risk_desc="安全策略绕过",
        )
        if deny_conflict:
            results.append(deny_conflict)

    return results


# ============================================================
# 主入口
# ============================================================

def check() -> list[CheckResult]:
    """settings_check 主入口。

    跑两段:
      1. 用户级 settings.json 检查 (v0.1.0 逻辑)
      2. 项目级 settings 冲突检测 (v1.0 新增)
    """
    results: list[CheckResult] = []
    results.extend(_check_user_settings())
    results.extend(_check_project_conflicts())
    return results
