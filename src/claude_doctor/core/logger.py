"""结构化日志（stderr，WARNING 级）。

照抄 omc_replica/core/logger.py:1-23 风格：单 logger、stderr 输出、WARNING 默认。
"""
from __future__ import annotations

import logging
import sys

_LOGGER_NAME = "claude_doctor"


def get_logger() -> logging.Logger:
    """获取 claude_doctor 全局 logger（带 stderr handler）。"""
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
    return logger