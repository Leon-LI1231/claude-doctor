"""mcp_check — MCP 服务器可执行性体检。

数据源：`~/.claude.json` 的 `projects.<cwd>.mcpServers`
  （注：`claude mcp list` 只看顶层 mcpServers / 项目级 .mcp.json，
   不看 `projects.<cwd>.mcpServers`，所以必须自己读 .claude.json）

对每个 (project, server) 检查：
  - command 字段是否存在
  - command 路径在磁盘上是否真的存在
"""
from __future__ import annotations

import json
from pathlib import Path

from ..locator import claude_json
from ..types import CheckResult, CheckStatus


def check() -> list[CheckResult]:
    """mcp_check 主入口。"""
    path = claude_json()
    results: list[CheckResult] = []

    if not path.exists():
        results.append(CheckResult(
            CheckStatus.WARN,
            "mcp.claude_json_exists",
            f"文件不存在: {path}",
        ))
        return results

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        results.append(CheckResult(
            CheckStatus.FAIL,
            "mcp.claude_json_valid",
            f"JSON 解析失败: {e}",
        ))
        return results

    projects = data.get("projects", {})
    if not isinstance(projects, dict) or not projects:
        results.append(CheckResult(
            CheckStatus.WARN,
            "mcp.no_projects",
            "~/.claude.json 中无 projects 记录",
        ))
        return results

    # 收集所有 MCP
    total_servers = 0
    for proj_path, proj_data in projects.items():
        if not isinstance(proj_data, dict):
            continue
        servers = proj_data.get("mcpServers", {})
        if not isinstance(servers, dict) or not servers:
            continue

        for srv_name, srv_conf in servers.items():
            total_servers += 1
            if not isinstance(srv_conf, dict):
                results.append(CheckResult(
                    CheckStatus.FAIL,
                    f"mcp.{proj_path}.{srv_name}",
                    "配置不是 dict",
                ))
                continue

            cmd = srv_conf.get("command", "")
            if not cmd:
                results.append(CheckResult(
                    CheckStatus.FAIL,
                    f"mcp.{proj_path}.{srv_name}",
                    "无 command 字段",
                ))
                continue

            cmd_path = Path(cmd)
            if cmd_path.exists():
                results.append(CheckResult(
                    CheckStatus.PASS,
                    f"mcp.{proj_path}.{srv_name}",
                    f"command 存在: {cmd}",
                ))
            else:
                results.append(CheckResult(
                    CheckStatus.FAIL,
                    f"mcp.{proj_path}.{srv_name}",
                    f"command 不存在: {cmd}",
                    {"missing_path": cmd, "project": proj_path},
                ))

    if total_servers == 0:
        results.append(CheckResult(
            CheckStatus.WARN,
            "mcp.no_servers",
            "无 MCP 服务器注册（projects[*].mcpServers 均为空）",
        ))

    return results