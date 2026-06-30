# claude-doctor — 项目指引

## 这是什么？

一个**纯本地 CLI 工具**，在 `cmd` 里一行 `claude-doctor check` 就能诊断 `~/.claude` 配置的健康度。

**3 个核心 check**：
- `env_check` —— 对比 process env / settings.json / Windows 注册表中的 `ANTHROPIC_*` 变量
- `settings_check` —— `~/.claude/settings.json` 合法性 + permissions.allow 审计
- `mcp_check` —— `~/.claude.json` 中注册的 MCP 服务器可执行性

**关键事实**：
| 项目 | 详情 |
|---|---|
| 依赖 | 仅 Python 3.10+ + `click>=8.1` + `rich>=13` |
| LLM/MCP 依赖 | **零** —— 纯本地探针 |
| 数据源 | `~/.claude.json` / `~/.claude/settings.json` / `HKCU\Environment` |
| 部署模板 | 完全照抄 [`omc-replica`](E:\OMC历史对话功能复刻\README.md) 的 venv + .cmd wrapper 模式 |
| 运行时目录 | `C:\Users\Lenovo\AppData\Local\Programs\claude-doctor\`（与源码物理隔离） |

## 项目结构

```
E:\claude-doctor\
├── README.md                # 顶层项目入口
├── CLAUDE.md                # 本文件（项目指引）
├── LICENSE                  # MIT
├── pyproject.toml           # 包元数据
├── .gitignore
├── src\
│   └── claude_doctor\       # 源码
│       ├── __init__.py      # __version__ = "0.1.0"
│       ├── __main__.py      # python -m claude_doctor
│       ├── cli.py           # click group + check/doctor/version
│       └── core\
│           ├── types.py     # CheckStatus / CheckResult / Report
│           ├── runner.py    # 编排器（双层 try/except 兜底）
│           ├── reporter.py  # table / json / md 输出
│           ├── locator.py   # 路径定位（支持 mock env var）
│           └── checks\
│               ├── env_check.py
│               ├── settings_check.py
│               └── mcp_check.py
├── deploy\                  # 占位（v0.5.0 加 offline wheel 脚本）
├── tests\                   # 占位（v0.2.0 加 pytest）
└── docs\                    # 占位
```

## 开发约定

- **新增 check**：在 `src/claude_doctor/core/checks/` 加文件，写 `check() -> list[CheckResult]`，再在 `core/checks/__init__.py` 的 `CHECK_REGISTRY` 注册。
- **不要硬编码**真实 `~/.claude.json` 路径 —— 用 `core.locator` 的 `claude_json()` / `settings_json()`，它们支持 `CLAUDE_DOCTOR_HOME` / `CLAUDE_DOCTOR_USERJSON` 环境变量覆盖。
- **TOKEN/KEY 字段必须 mask**：用 `env_check._mask()`，报告可分享。
- **注释详细**：本项目给"新人"看，函数 docstring 写明意图、参数、返回、抛错。

## 验证

```bash
# 1) import 验证
PYTHONPATH=E:\claude-doctor\src python -c "import claude_doctor; print(claude_doctor.__version__)"
# 预期: 0.1.0

# 2) CLI 验证
"C:\Users\Lenovo\AppData\Local\Programs\claude-doctor\venv\Scripts\python.exe" -m claude_doctor.cli check
# 预期: 终端表格 + 总结行
```

## 与 omc-replica 的关系

- 部署模板（venv + .cmd wrapper）**照抄** omc-replica
- 注释里的"参考 omc-replica"是**血统证明**，不是模块依赖
- 两个项目**完全独立**，无运行时耦合
- 源码物理上在 `E:\claude-doctor\`，omc-replica 在 `E:\OMC历史对话功能复刻\`
