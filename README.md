# claude-doctor

> **Claude Code 体检医生** —— 在 `cmd` 里一行命令，扫出你 `.claude` 目录里"看不见的病"。

[![version](https://img.shields.io/badge/version-0.1.0-blue.svg)]()
[![python](https://img.shields.io/badge/python-3.10%2B-blue.svg)]()
[![license](https://img.shields.io/badge/license-MIT-green.svg)]()

---

## 这是什么？

`claude-doctor` 是一个**纯本地 CLI 工具**，专门诊断 `~/.claude/` 和 `~/.claude.json` 的健康度。它不依赖 LLM、不依赖 MCP、不联网，**10 毫秒内**给出可执行的修复建议。

**典型用户场景**：

| 你遇到的问题 | 医生怎么帮你 |
|---|---|
| "我的 MCP 服务器突然连不上了" | `mcp_check` 抓出 command 路径不存在 |
| "settings.json 写了 env 为什么没生效？" | `env_check` 对比 process / settings / registry，告诉你漂移点 |
| "每次启动 Claude Code 都要点一堆确认" | `settings_check` 检查 permissions.allow 是否被配空了 |
| "同事说他那边能跑我这边不行" | `--report` 落盘 Markdown，发给同事对比 |

**它和 OMC / `omc-replica` 是什么关系**？

- `omc-replica` 是**搜索历史会话**（读 `~/.claude/projects/*.jsonl`）
- `claude-doctor` 是**诊断配置健康**（读 `~/.claude.json` / `settings.json` / 注册表）
- 两者**完全独立部署**，互不依赖，互不干扰
- 部署模式、wrapper 模板、Python venv 结构**完全一致**，便于团队统一维护

---

## 快速上手

### 安装（已预装到这台机器）

```cmd
> claude-doctor --version
claude-doctor, version 0.1.0
```

### 跑一次完整体检

```cmd
> claude-doctor check
```

### 只想查某一项

```cmd
> claude-doctor check --only env          # 只查环境变量
> claude-doctor check --only settings     # 只查 settings.json
> claude-doctor check --only mcp          # 只查 MCP 服务器
```

### 输出格式

```cmd
> claude-doctor check --format table      # 默认：彩色终端表格
> claude-doctor check --format json       # 给程序消费
> claude-doctor check --format md         # 纯 Markdown
```

### 落盘报告

```cmd
> claude-doctor check --report C:\reports\health.md
```

终端显示 + 落盘一份 Markdown 一气呵成。

### 退出码

| 状态 | 退出码 | 含义 |
|---|---|---|
| PASS / WARN | 0 | 健康（或可关注） |
| FAIL | 1 | 有致命问题，建议修复 |
| ERROR | 0 | check 自身挂了（**不影响**退出码，便于 CI 串联） |

---

## 实测：在这台机器上的首次跑

```
[Claude Doctor v0.1.0 — 体检报告]
─────────────────────────────────────────────────────────────────
[PASS] env.process.ANTHROPIC_BASE_URL       → 已设置: https://api.minimaxi.com/anthropic
[PASS] env.process.ANTHROPIC_AUTH_TOKEN     → 已设置: sk-cp-Ks***
[PASS] env.process.ANTHROPIC_DEFAULT_HAIKU_MODEL  → 已设置: minimax-m3
[PASS] env.process.ANTHROPIC_DEFAULT_SONNET_MODEL → 已设置: minimax-m3
[PASS] env.process.ANTHROPIC_DEFAULT_OPUS_MODEL   → 已设置: minimax-m3
[PASS] settings.json_valid                  → JSON 合法（4 个顶层键）
[WARN] settings.permissions.allow           → 6 条规则（含通配符 5 条: ['Bash(find:*)', ...]）
[PASS] mcp.C:/Users/Lenovo.omc-replica      → command 存在: ...\session-search-mcp.cmd
[PASS] mcp.E:/.omc-replica                  → command 存在: ...\session-search-mcp.cmd
─────────────────────────────────────────────────────────────────
总结: 8 通过 / 1 警告 / 0 失败 / 0 错误
```

> 输出里的"乱码"是 bash 终端的 GBK 编码问题；在真实 cmd 窗口里（系统默认 GBK 代码页）会正常显示中文。

---

## 三个 check 在查什么？

| Check | 体检目标 | 典型症状 |
|---|---|---|
| 🩺 `env_check` | **环境变量一致性** | 模型被 proxy 切换 / TOKEN 在三个地方不同步 / 配置漂移 |
| 🩺 `settings_check` | **配置文件合法性 + 权限策略** | 写错 JSON 启动就崩 / permissions.allow 空导致每次确认 / 误用通配符 |
| 🩺 `mcp_check` | **MCP 服务器可执行性** | 装了 MCP 但 command 路径被删 / 卸载工具后 .claude.json 没清干净 |

> **3 个 check × 多条结果 = 报告**。`--only` 多次传可只跑某个 check。

---

## 系统设计

### 总体架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                          用户 (cmd / PowerShell)                       │
│                              │                                       │
│                              ▼                                       │
│         ┌────────────────────────────────────────────┐               │
│         │  bin\claude-doctor.cmd  (5 行 wrapper)    │               │
│         │   set CLAUDE_DOCTOR_PY=...\python.exe      │               │
│         │   %CLAUDE_DOCTOR_PY% -m claude_doctor.cli %* │             │
│         └────────────────────┬───────────────────────┘               │
│                              │                                       │
│                              ▼                                       │
│         ┌────────────────────────────────────────────┐               │
│         │  cli.py  (Click Group)                     │               │
│         │   -- claude-doctor --version                │               │
│         │   -- claude-doctor check [opts]             │               │
│         │   -- claude-doctor doctor   (alias)         │               │
│         └────────────────────┬───────────────────────┘               │
│                              │ invoke check                          │
│                              ▼                                       │
│         ┌────────────────────────────────────────────┐               │
│         │  core/runner.py  (编排器)                  │               │
│         │   遍历 CHECK_REGISTRY, 调每个 check()      │               │
│         │   双层 try/except 兜底                      │               │
│         └─┬──────────────┬──────────────┬────────────┘               │
│           │              │              │                            │
│           ▼              ▼              ▼                            │
│      ┌─────────┐    ┌──────────┐    ┌─────────┐                     │
│      │ env_    │    │ settings_│    │  mcp_   │   core/checks/      │
│      │ check   │    │ check    │    │  check  │   (3 个独立模块)     │
│      └────┬────┘    └─────┬────┘    └────┬────┘                     │
│           │               │              │                          │
│           ▼               ▼              ▼                          │
│      ┌─────────┐    ┌──────────┐    ┌──────────┐                   │
│      │ 进程    │    │ settings │    │.claude   │  数据源             │
│      │ os.env  │    │   .json  │    │  .json   │  (3 个只读源)      │
│      │  +winreg│    │          │    │projects.*│                    │
│      └────┬────┘    └─────┬────┘    └────┬────┘                     │
│           │               │              │                          │
│           └───────────────┴──────────────┘                          │
│                              │                                       │
│                              ▼ list[CheckResult]                    │
│         ┌────────────────────────────────────────────┐               │
│         │  core/reporter.py  (3 种输出)              │               │
│         │   ┌──────┐  ┌──────┐  ┌──────┐             │               │
│         │   │table │  │ json │  │  md  │             │               │
│         │   │rich  │  │dict  │  │.md   │             │               │
│         │   └──────┘  └──────┘  └──────┘             │               │
│         └────────────────────┬───────────────────────┘               │
│                              │                                       │
│                              ▼                                       │
│                          终端 / 文件                                  │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### Check 数据流

```
                   ┌─────────────────────────────────────────┐
                   │           run_checks(only=None)         │
                   │                                          │
                   │  1. datetime.now() → started_at          │
                   │  2. for name in CHECK_REGISTRY:          │
                   │  3.   try: check_module.check()          │
                   │  4.   except: CheckResult(ERROR)         │
                   │  5. datetime.now() → finished_at         │
                   │  6. return Report(results=...)           │
                   └────────────────┬────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
   ┌─────────────────┐   ┌─────────────────────┐   ┌──────────────────┐
   │  env_check()    │   │  settings_check()   │   │   mcp_check()    │
   │                 │   │                     │   │                  │
   │ 读 3 处 ANTHRO  │   │ 读 ~/.claude/       │   │ 读 ~/.claude.json│
   │ PIC_* 变量:     │   │ settings.json       │   │ projects.*.mcp   │
   │                 │   │                     │   │ Servers          │
   │ ① process env  │   │ ① JSON 合法性       │   │                  │
   │    os.environ   │   │ ② 顶层键白名单      │   │ ① command 存在性 │
   │ ② settings.json │   │ ③ permissions.allow │   │    Path.exists() │
   │    env 块       │   │     - 数量          │   │                  │
   │ ③ registry      │   │     - 通配符检测    │   │                  │
   │    winreg       │   │     - allow/deny    │   │                  │
   │    HKCU\Env     │   │       冲突检测      │   │                  │
   │                 │   │                     │   │                  │
   │ 输出:           │   │ 输出:               │   │ 输出:            │
   │  N 条 Check     │   │  1~3 条 Check       │   │  N 条 Check      │
   │  Result         │   │  Result             │   │  Result          │
   └────────┬────────┘   └──────────┬──────────┘   └────────┬─────────┘
            │                       │                       │
            └───────────────────────┴───────────────────────┘
                                    │
                                    ▼
                   ┌─────────────────────────────────────────┐
                   │           runner.run_checks()            │
                   │                                          │
                   │  合并所有 CheckResult → Report           │
                   │                                          │
                   │  Report:                                 │
                   │   - results: list[CheckResult]           │
                   │   - started_at: ISO 8601                 │
                   │   - finished_at: ISO 8601                │
                   │   - exit_code: 1 if any FAIL else 0      │
                   └────────────────┬────────────────────────┘
                                    │
                                    ▼
                   ┌─────────────────────────────────────────┐
                   │           reporter                       │
                   │                                          │
                   │  render_table(report) → rich.Table       │
                   │  render_json(report)  → dict             │
                   │  render_markdown(report) → .md           │
                   └─────────────────────────────────────────┘
```

### CheckResult 数据结构

```python
@dataclass
class CheckResult:
    status: CheckStatus      # PASS / WARN / FAIL / ERROR
    name: str                # "env.process.ANTHROPIC_BASE_URL"
    message: str             # "已设置: https://api.minimaxi.com/anthropic"
    detail: dict[str, Any]   # {"source": "process"}  (可选, 给 --format json 用)


class CheckStatus(str, Enum):
    PASS  = "pass"    # 通过
    WARN  = "warn"    # 警告 (不致命)
    FAIL  = "fail"    # 失败 (致命, 退出码 = 1)
    ERROR = "error"   # check 自身挂了 (不影响退出码)
```

### 异常处理双层兜底

```
        check() 函数                     runner.run_checks()
        ────────────                     ──────────────────
        ┌──────────────┐                ┌──────────────────┐
        │  try:        │                │  for name in ...: │
        │    业务逻辑   │                │    try:           │
        │    return    │                │      check()      │ ← check 内部已 try/except
        │    CheckResult│                │    except:        │
        │  except:     │                │      CheckResult  │ ← runner 再兜底
        │    return    │                │      (ERROR)      │
        │    CheckResult│ ← check 自己 │                  │
        │    (ERROR)   │   也不抛       └──────────────────┘
        └──────────────┘
```

> 即便 check 作者忘了 `try/except`，runner 也会兜底生成 ERROR 结果，不让整个工具挂掉。

### 部署架构（仿 omc-replica 模板）

```
C:\Users\Lenovo\AppData\Local\Programs\claude-doctor\
│
├── bin\
│   └── claude-doctor.cmd                # 5 行 wrapper, 调 venv\Scripts\python.exe
│                                          (照抄 omc-replica\bin\session-search.cmd)
│
└── venv\
    ├── pyvenv.cfg                       # 基于 C:\Python314\python.exe
    ├── Include/
    ├── Lib\site-packages\
    │   ├── click-8.4.2.dist-info/       # 运行时依赖
    │   ├── rich-15.0.0.dist-info/
    │   └── claude_doctor\               # 14 个 .py 源码
    │       ├── __init__.py              # __version__ = "0.1.0"
    │       ├── __main__.py              # python -m claude_doctor 入口
    │       ├── cli.py                   # click group
    │       └── core\
    │           ├── types.py             # CheckStatus / CheckResult / Report
    │           ├── exceptions.py
    │           ├── logger.py
    │           ├── locator.py           # 路径定位 (支持 env var mock)
    │           ├── runner.py            # 编排器
    │           ├── reporter.py          # 3 种输出格式
    │           └── checks\
    │               ├── env_check.py
    │               ├── settings_check.py
    │               └── mcp_check.py
    └── Scripts\python.exe               # venv 内 Python 解释器
                                           ↑
                                  wrapper 通过绝对路径调用

注册表 HKCU\Environment\Path:
  C:\...\Microsoft VS Code\bin;
  C:\...\omc-replica\bin;                ← 已存在
  C:\...\claude-doctor\bin               ← 新增
```

---

## 关键设计决策

| 决策 | 选择 | 理由 |
|---|---|---|
| **完全照抄 omc-replica 部署模板** | venv + .cmd wrapper + 注册表 PATH | 0 学习成本，0 风险 |
| **CLI 而非 MCP/Sub-agent** | 独立可执行 | 不依赖 Claude Code 本身，跨工具可复用 |
| **click 而非 argparse** | 8.4.2 | 团队熟悉，group + subcommand 模式清晰 |
| **rich 而非纯 ANSI** | 15.0.0 | 表格+颜色，体检报告体感提升明显 |
| **4 态 CheckStatus** | PASS/WARN/FAIL/ERROR | 区分"配错" vs "我没检查出来" |
| **WARN 不影响退出码** | 0 vs 1 | 便于 `&&` 串联 |
| **TOKEN/KEY 自动 mask** | 前 8 字符 + `***` | 报告可分享不泄露 |
| **直接读 .claude.json** | 而非 `claude mcp list` | 那个命令漏看 `projects.<cwd>.mcpServers` |
| **locator 支持 mock 环境变量** | `CLAUDE_DOCTOR_HOME` / `CLAUDE_DOCTOR_USERJSON` | 不污染真实配置，单元测试可用 |
| **不引入 jsonschema** | MVP 阶段手写 if  | 简单可控；v0.2 再考虑 |
| **不读 .jsonl 内容** | 只看 env/settings/.claude.json | 体检 ≠ 搜索，职责分离 |

---

## 项目结构

```
src/claude_doctor/                    ← 源码根
├── __init__.py                       # __version__
├── __main__.py                       # python -m claude_doctor 入口
├── cli.py                            # click group + 3 子命令
├── README.md                         # 本文件
└── core/
    ├── __init__.py
    ├── types.py                      # CheckStatus / CheckResult / Report
    ├── exceptions.py                 # ClaudeDoctorError
    ├── logger.py                     # stderr logger
    ├── locator.py                    # 路径定位 (env var mock)
    ├── runner.py                     # 编排 + 双层 try/except
    ├── reporter.py                   # table / json / md 输出
    └── checks/
        ├── __init__.py               # CHECK_REGISTRY
        ├── env_check.py              # process / settings / registry 三处对比
        ├── settings_check.py         # JSON 合法 + permissions 审计
        └── mcp_check.py              # projects[*].mcpServers.command 检查
```

---

## 开发与扩展

### 本地开发模式

```bash
# 在 src/ 目录下
cd E:\claude-doctor
pip install -e .

# 跑（用 venv 内的 python）
"C:\Users\Lenovo\AppData\Local\Programs\claude-doctor\venv\Scripts\python.exe" -m claude_doctor.cli check
```

### 新增一个 check

1. 在 `core/checks/` 下加一个 `xxx_check.py`
2. 写一个 `check() -> list[CheckResult]` 函数
3. 在 `core/checks/__init__.py` 的 `CHECK_REGISTRY` 注册

模板：

```python
from ..types import CheckResult, CheckStatus


def check() -> list[CheckResult]:
    """xxx_check — 一句话说清在查什么。"""
    results: list[CheckResult] = []
    try:
        # 业务逻辑
        results.append(CheckResult(CheckStatus.PASS, "xxx.name", "..."))
    except Exception as e:
        results.append(CheckResult(CheckStatus.ERROR, "xxx.name", f"检查失败: {e}"))
    return results
```

### 测试（带 mock）

利用 `CLAUDE_DOCTOR_HOME` / `CLAUDE_DOCTOR_USERJSON` 环境变量，**不污染真实配置**：

```bash
# 准备 mock 数据
mkdir -p /tmp/test/.claude
cat > /tmp/test/.claude.json <<'EOF'
{"projects": {"MOCK": {"mcpServers": {"dead": {"command": "C:/none.exe"}}}}}
EOF

# 跑 mcp_check
CLAUDE_DOCTOR_HOME=/tmp/test/.claude CLAUDE_DOCTOR_USERJSON=/tmp/test/.claude.json \
  python -m claude_doctor.cli check --only mcp
# 预期: 1 FAIL, exit 1
```

---

## 路线图

| 版本 | 范围 | 状态 |
|---|---|---|
| v0.1.0 | env / settings / mcp 三个核心 check | ✅ 已发布 |
| v0.2.0 | + permissions / transcript / disk 三个 check | 计划中 |
| v0.3.0 | + `claude-doctor fix` 自动修复（带确认提示） | 计划中 |
| v0.4.0 | + MCP server 集成（仿 `omc-replica` 的 mcp_server.py）| 计划中 |
| v0.5.0 | + 离线 wheel 打包（`prepare-offline.ps1` 等） | 计划中 |
| v1.0.0 | + 单元测试 + 跨平台 + GitHub release | 计划中 |

---

## 故障排查

### Q: 中文乱码？
A: bash 终端的 GBK 编码问题。在真实 cmd 窗口（系统默认 GBK）会正常显示。或者用 `--format json` / `--format md` 落盘查看。

### Q: `claude-doctor: command not found`？
A: PATH 已写入 `HKCU\Environment` 但当前 shell 没刷新。**重开 cmd** 即可。或用绝对路径：
```cmd
> C:\Users\Lenovo\AppData\Local\Programs\claude-doctor\bin\claude-doctor.cmd --version
```

### Q: 卸载？
A: 删除 `C:\Users\Lenovo\AppData\Local\Programs\claude-doctor\` 整个目录，再从 `HKCU\Environment\Path` 移除 `;C:\Users\Lenovo\AppData\Local\Programs\claude-doctor\bin`。venv 是完全隔离的，不影响其他 Python 环境。

### Q: 升级？
A: 没有升级器（v0.1.0 没有）。后续版本会加 `claude-doctor update` 子命令。

---

## 与 omc-replica 的关系

| 维度 | omc-replica | claude-doctor |
|---|---|---|
| 数据源 | `~/.claude/projects/*.jsonl` | `~/.claude.json` / `settings.json` / 注册表 |
| 工具名（CLI） | `session-search` | `claude-doctor` |
| 工具名（Python） | `omc_replica` | `claude_doctor` |
| 部署目录 | `~\AppData\Local\Programs\omc-replica\` | `~\AppData\Local\Programs\claude-doctor\` |
| 部署模板 | 同款 venv + .cmd wrapper | 同款 venv + .cmd wrapper |
| 可共存 | ✅ | ✅ |
| 互不依赖 | ✅ | ✅ |

---

## 许可证

MIT