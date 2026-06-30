"""`python -m claude_doctor` 入口。

和 `python -m claude_doctor.cli` 等价（保留 omc-replica 风格的双入口）。
"""
from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())