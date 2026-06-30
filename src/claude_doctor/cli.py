"""claude-doctor CLI 入口。

命令结构：
  claude-doctor                  # 默认 → check
  claude-doctor --version
  claude-doctor check [options]  # 跑全部（或指定）check
  claude-doctor doctor           # check 的友好别名

参考 omc-replica 的 click group 模式（cli.py:39-51）。
"""
from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from . import __version__
from .core.exceptions import ClaudeDoctorError
from .core.logger import get_logger
from .core.reporter import render_json, render_markdown, render_table
from .core.runner import run_checks

logger = get_logger()
console = Console()


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="claude-doctor")
@click.option("-v", "--verbose", is_flag=True, help="详细日志 (DEBUG 级)")
@click.option("--format", "fmt", type=click.Choice(["table", "json", "md"]),
              default="table", help="输出格式 (默认 table)")
@click.option("--only", "only", multiple=True,
              help="只跑指定 check（可多次传：--only env --only mcp）")
@click.option("--report", "report_path", type=click.Path(),
              help="落盘 Markdown 报告到指定路径")
@click.pass_context
def main(
    ctx: click.Context,
    verbose: bool,
    fmt: str,
    only: tuple[str, ...],
    report_path: str | None,
) -> None:
    """Claude Code 体检医生 — 诊断 ~/.claude 配置健康度。"""
    if verbose:
        logger.setLevel("DEBUG")
    if ctx.invoked_subcommand is None:
        # 不带子命令时默认跑 check
        ctx.invoke(check, fmt=fmt, only=only, report_path=report_path)


@main.command()
@click.option("--format", "fmt", type=click.Choice(["table", "json", "md"]), default="table")
@click.option("--only", "only", multiple=True,
              help="只跑指定 check（可多次传）")
@click.option("--report", "report_path", type=click.Path(),
              help="落盘 Markdown 报告到指定路径")
def check(
    fmt: str,
    only: tuple[str, ...],
    report_path: str | None,
) -> None:
    """跑全部（或指定）健康检查。"""
    try:
        result = run_checks(only=list(only) if only else None)
    except ClaudeDoctorError as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        sys.exit(1)

    # 终端输出
    if fmt == "table":
        click.echo(render_table(result))
    elif fmt == "json":
        click.echo(render_json(result))
    elif fmt == "md":
        click.echo(render_markdown(result))

    # 落盘（始终写 Markdown，方便事后查阅）
    if report_path:
        report_file = Path(report_path)
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(render_markdown(result), encoding="utf-8")
        # 提示用纯 ASCII 字符，避免在 GBK 终端（默认 cmd）崩溃
        console.print(f"[bold green][OK] 报告已保存: {report_path}[/bold green]")

    # 退出码：FAIL → 1，否则 0
    sys.exit(result.exit_code)


@main.command()
@click.option("--format", "fmt", type=click.Choice(["table", "json", "md"]), default="table")
@click.option("--only", "only", multiple=True)
@click.option("--report", "report_path", type=click.Path())
def doctor(
    fmt: str,
    only: tuple[str, ...],
    report_path: str | None,
) -> None:
    """check 的友好别名（给新人更直觉的入口）。"""
    ctx = click.get_current_context()
    ctx.invoke(check, fmt=fmt, only=only, report_path=report_path)


@main.command()
def version() -> None:
    """输出版本号。"""
    click.echo(f"claude-doctor {__version__}")


if __name__ == "__main__":
    sys.exit(main())