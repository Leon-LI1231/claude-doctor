"""核心数据类型：CheckStatus / CheckResult / Report。"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CheckStatus(str, Enum):
    """检查结果状态。

    - PASS:  通过
    - WARN:  警告（不致命，建议关注）
    - FAIL:  失败（致命，建议修复）
    - ERROR: 检查自身异常（check 函数挂了）
    """

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    ERROR = "error"


@dataclass
class CheckResult:
    """单条 check 的结果。

    Attributes:
        status:  状态
        name:    检查项名（如 "env.process.ANTHROPIC_BASE_URL"）
        message: 人类可读的一句话
        detail:  结构化详情（可选，方便 --format json 输出）
    """

    status: CheckStatus
    name: str
    message: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    """完整体检报告。"""

    results: list[CheckResult]
    started_at: str  # ISO 8601
    finished_at: str  # ISO 8601

    @property
    def exit_code(self) -> int:
        """有 FAIL → 1，否则 0。WARN 不影响退出码。"""
        return 1 if any(r.status == CheckStatus.FAIL for r in self.results) else 0

    def to_dict(self) -> dict[str, Any]:
        """转 JSON-serializable dict（给 --format json 用）。"""
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "summary": {
                "pass": sum(1 for r in self.results if r.status == CheckStatus.PASS),
                "warn": sum(1 for r in self.results if r.status == CheckStatus.WARN),
                "fail": sum(1 for r in self.results if r.status == CheckStatus.FAIL),
                "error": sum(1 for r in self.results if r.status == CheckStatus.ERROR),
            },
            "results": [
                {
                    "status": r.status.value,
                    "name": r.name,
                    "message": r.message,
                    "detail": r.detail,
                }
                for r in self.results
            ],
        }