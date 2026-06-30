"""定位关键文件路径。

当前 MVP 阶段所有路径都是写死的 `~/.claude` 和 `~/.claude.json`，
未来要做跨平台/MultiHome 时再扩展。
"""
from __future__ import annotations

import os
from pathlib import Path


def claude_home() -> Path:
    """`~/.claude` 目录（Claude Code 用户级数据目录）。

    可通过 `CLAUDE_DOCTOR_HOME` 环境变量覆盖（方便 mock 测试）。
    """
    override = os.environ.get("CLAUDE_DOCTOR_HOME")
    if override:
        return Path(override)
    return Path.home() / ".claude"


def claude_json() -> Path:
    """`~/.claude.json`（Claude Code 用户级配置中心，含 projects & mcpServers）。

    可通过 `CLAUDE_DOCTOR_USERJSON` 环境变量覆盖（方便 mock 测试）。
    """
    override = os.environ.get("CLAUDE_DOCTOR_USERJSON")
    if override:
        return Path(override)
    return Path.home() / ".claude.json"


def settings_json() -> Path:
    """`~/.claude/settings.json`（Claude Code 用户级 settings）。"""
    return claude_home() / "settings.json"


def projects_dir() -> Path:
    """`~/.claude/projects/`（每个 cwd 一个子目录，存放 .jsonl transcript）。"""
    return claude_home() / "projects"