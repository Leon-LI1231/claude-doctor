"""runner — 编排所有 check，生成 Report。

设计要点（来自 omc-replica 模式）：
  - 双层 try/except 兜底：check() 内部 try/except + runner 再 try/except
  - 即便某个 check 函数忘记 try/except 自己抛了，runner 也能生成 ERROR 结果
  - `--only` 多次传：只跑指定的 check
"""
from __future__ import annotations

from datetime import datetime, timezone

from .checks import CHECK_REGISTRY
from .exceptions import ClaudeDoctorError
from .types import CheckResult, CheckStatus, Report


def run_checks(only: list[str] | None = None) -> Report:
    """跑指定（或全部）check，生成 Report。

    Args:
        only: 要跑的 check 名列表。None = 跑全部。

    Returns:
        Report（永不抛异常，除非 ClaudeDoctorError 这种配置错误）。
    """
    started = datetime.now(timezone.utc).isoformat()
    all_results: list[CheckResult] = []

    targets = list(only) if only else list(CHECK_REGISTRY.keys())

    for name in targets:
        if name not in CHECK_REGISTRY:
            all_results.append(CheckResult(
                CheckStatus.ERROR,
                f"runner.{name}",
                f"未知 check: {name}（可用: {', '.join(CHECK_REGISTRY.keys())}）",
            ))
            continue
        try:
            check_module = CHECK_REGISTRY[name]
            results = check_module.check()
            all_results.extend(results)
        except Exception as e:
            # 双层兜底：check() 自己没 try/except 时，runner 兜底
            all_results.append(CheckResult(
                CheckStatus.ERROR,
                f"runner.{name}",
                f"check() 自身抛异常: {e}",
            ))

    finished = datetime.now(timezone.utc).isoformat()
    return Report(results=all_results, started_at=started, finished_at=finished)