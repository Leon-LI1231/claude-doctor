"""定位关键文件路径。

当前 MVP 阶段所有路径都是写死的 `~/.claude` 和 `~/.claude.json`，
未来要做跨平台/MultiHome 时再扩展。
"""  # noqa: D202, D205
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


# ============================================================
# v1.0 新增：项目级 settings 定位
# ============================================================

# 项目级 settings 文件的相对路径（位于 `.claude/` 子目录下）
_PROJECT_SETTINGS = Path(".claude") / "settings.json"
_PROJECT_LOCAL_SETTINGS = Path(".claude") / "settings.local.json"


def find_project_settings(
    cwd: Path | str | None = None,
) -> tuple[Path, Path]:
    r"""从 cwd 向上找项目级 settings 文件（最多到文件系统根）。

    搜索规则（按优先级）：
      1. 找到第一个两个文件都存在的目录，立即返回
      2. 找到第一个 settings.json（项目级）存在的目录，返回
         （包括 settings.local.json 不存在的情况；冲突检测会用 exists() 判断）
      3. 找到第一个 settings.local.json 存在的目录，返回
         （包括 settings.json 不存在的情况）
      4. 都没找到，返回 start 下的期望路径（不报错）

    Args:
        cwd: 起始目录，None = 当前工作目录。

    Returns:
        (project_settings_path, project_local_settings_path) 元组。
        路径不保证文件存在，请用 path.exists() 判断。

    样例:
        >>> find_project_settings("E:/claude-doctor")
        (WindowsPath('E:/claude-doctor/.claude/settings.json'),
         WindowsPath('E:/claude-doctor/.claude/settings.local.json'))

        >>> find_project_settings("C:/no/such/dir")
        (WindowsPath('C:/no/such/dir/.claude/settings.json'),
         WindowsPath('C:/no/such/dir/.claude/settings.json'))
    """
    start = Path(cwd) if cwd else Path.cwd()
    # 兼容 start 本身是文件的情况（取父目录）
    if start.is_file():
        start = start.parent

    # 1) 优先找两个文件都存在的目录
    for current in [start, *start.parents]:
        project = current / _PROJECT_SETTINGS
        local = current / _PROJECT_LOCAL_SETTINGS
        if project.exists() and local.exists():
            return (project, local)

    # 2) 找第一个 settings.json 存在的目录
    for current in [start, *start.parents]:
        project = current / _PROJECT_SETTINGS
        if project.exists():
            return (project, current / _PROJECT_LOCAL_SETTINGS)

    # 3) 找第一个 settings.local.json 存在的目录
    for current in [start, *start.parents]:
        local = current / _PROJECT_LOCAL_SETTINGS
        if local.exists():
            return (current / _PROJECT_SETTINGS, local)

    # 4) 都没找到 → 返回 start 下的期望路径（不报错）
    return (start / _PROJECT_SETTINGS, start / _PROJECT_LOCAL_SETTINGS)