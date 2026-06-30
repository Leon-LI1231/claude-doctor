"""reporter — Report → 终端表格 / JSON / Markdown。

终端默认走 rich（彩色 + Table）；JSON/Markdown 走纯文本。
"""
from __future__ import annotations

import io
import json
import sys
from typing import Any

from .types import CheckStatus, Report

# ANSI 颜色码（仅 fallback 路径；正常用 rich）
_ANSI = {
    CheckStatus.PASS: "\033[32m",   # 绿
    CheckStatus.WARN: "\033[33m",   # 黄
    CheckStatus.FAIL: "\033[31m",   # 红
    CheckStatus.ERROR: "\033[35m",  # 紫
}
_RESET = "\033[0m"
_BOLD = "\033[1m"

_ICON = {
    CheckStatus.PASS:  "[PASS]",
    CheckStatus.WARN:  "[WARN]",
    CheckStatus.FAIL:  "[FAIL]",
    CheckStatus.ERROR: "[ERR ]",
}


def _try_rich():
    """尝试 import rich；失败返回 None。"""
    try:
        from rich.console import Console
        from rich.table import Table
        return Console, Table
    except ImportError:
        return None


def render_table(report: Report) -> str:
    """渲染为终端表格（带颜色）。"""
    summary = report.to_dict()["summary"]
    title = f"Claude Doctor v{_get_version()} — 体检报告"

    Console, Table = _try_rich()
    if Console and Table:
        buf = io.StringIO()
        console = Console(file=buf, force_terminal=True, color_system="truecolor")
        table = Table(title=title, show_lines=False, header_style="bold")
        table.add_column("状态", style="bold", width=10, no_wrap=True)
        table.add_column("检查项", width=50, overflow="fold")
        table.add_column("信息", overflow="fold")

        for r in report.results:
            style = {
                CheckStatus.PASS:  "bold green",
                CheckStatus.WARN:  "bold yellow",
                CheckStatus.FAIL:  "bold red",
                CheckStatus.ERROR: "bold magenta",
            }[r.status]
            table.add_row(f"[{style}]{_ICON[r.status]}[/{style}]", r.name, r.message)

        console.print(table)
        console.print(
            f"─── 总结: [green]{summary['pass']} 通过[/green] / "
            f"[yellow]{summary['warn']} 警告[/yellow] / "
            f"[red]{summary['fail']} 失败[/red] / "
            f"[magenta]{summary['error']} 错误[/magenta] ───"
        )
        return buf.getvalue()
    else:
        # Fallback: ANSI 颜色
        lines = [f"{_BOLD}{title}{_RESET}", ""]
        for r in report.results:
            color = _ANSI[r.status]
            lines.append(f"{color}{_ICON[r.status]}{_RESET} {r.name:<50} {r.message}")
        lines.append("")
        s = summary
        lines.append(
            f"─── 总结: {_ANSI[CheckStatus.PASS]}{s['pass']} 通过{_RESET} / "
            f"{_ANSI[CheckStatus.WARN]}{s['warn']} 警告{_RESET} / "
            f"{_ANSI[CheckStatus.FAIL]}{s['fail']} 失败{_RESET} / "
            f"{_ANSI[CheckStatus.ERROR]}{s['error']} 错误{_RESET} ───"
        )
        return "\n".join(lines)


def render_json(report: Report) -> str:
    """渲染为 JSON（中文不转义）。"""
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)


def render_markdown(report: Report) -> str:
    """渲染为 Markdown（适合落盘 + 邮件 + Issue）。"""
    s = report.to_dict()["summary"]
    lines = [
        f"# Claude Doctor v{_get_version()} 体检报告",
        "",
        f"- **开始**: {report.started_at}",
        f"- **完成**: {report.finished_at}",
        f"- **总结**: {s['pass']} 通过 / {s['warn']} 警告 / {s['fail']} 失败 / {s['error']} 错误",
        "",
        "| 状态 | 检查项 | 信息 |",
        "|------|--------|------|",
    ]
    for r in report.results:
        lines.append(f"| {_ICON[r.status]} | `{r.name}` | {r.message} |")
    lines.append("")
    return "\n".join(lines)


def _get_version() -> str:
    """读 package 版本（延迟导入避免循环）。"""
    from claude_doctor import __version__
    return __version__