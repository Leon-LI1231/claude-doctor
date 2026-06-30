# Changelog

本项目的所有显著变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [0.1.0] - 2026-06-30

### Added（新增）

- **首个公开版本**。从设计到部署到 GitHub 全流程完成。
- **3 个核心 check**：
  - `env_check` —— 对比 process env / `settings.json` env 块 / Windows 注册表 `HKCU\Environment` 中的 `ANTHROPIC_*` 变量，输出 1~3 条 CheckResult / 变量
  - `settings_check` —— 验证 `~/.claude/settings.json` 合法性 + `permissions.allow` 审计（数量 / 通配符 / allow-vs-deny 冲突）
  - `mcp_check` —— 遍历 `~/.claude.json` 的 `projects[*].mcpServers`，验证每个 `command` 路径是否还存在
- **4 态 CheckStatus**：`PASS` / `WARN` / `FAIL` / `ERROR`，WARN 不影响退出码、FAIL→1
- **3 种报告输出**：`table`（rich 彩色表格，默认）/ `json` / `md`
- **`--report <path>`** 同时终端输出 + 落盘 Markdown
- **`--only <name>`** 多次传可只跑某个 check
- **`--format`** 切换输出格式
- **`doctor` 子命令**（`check` 的友好别名）
- **环境变量 mock**：`CLAUDE_DOCTOR_HOME` / `CLAUDE_DOCTOR_USERJSON` 支持覆盖默认路径，方便测试不污染真实配置
- **TOKEN/KEY 自动 mask**（前 8 字符 + `***`），报告可分享不泄露
- **双层 try/except 兜底**：check 内部 + runner 再 try/except
- **运行时不依赖 LLM/MCP**：纯本地探针，10 毫秒出结果
- **完整文档**：
  - 顶层 README（461 行，4 张 ASCII 系统设计图）
  - CLAUDE.md（项目指引，给 Claude Code 看）
  - pyproject.toml（包元数据）
  - LICENSE（MIT）

### Deployment（部署）

- **运行时目录**：`C:\Users\Lenovo\AppData\Local\Programs\claude-doctor\`
  - 基于 `C:\Python314\python.exe` 创建 venv
  - 安装 `click>=8.1` + `rich>=13.0`
  - `bin\claude-doctor.cmd` 5 行 wrapper
  - `HKCU\Environment\Path` 已追加 `claude-doctor\bin`
- **项目根**：`E:\claude-doctor\`（独立，与 omc-replica 完全解耦）
- **GitHub**：`https://github.com/Leon-LI1231/claude-doctor`（已 push，commit `00994c6`）

### Verified（验证）

- 10 项端到端验证（V1-V10）全过
- 真实机器首次体检：**8 PASS / 1 WARN / 0 FAIL / 0 ERROR**
- omc-replica 回归冒烟通过：`session-search, version 1.0.0` 仍工作
- mock 环境验证 FAIL 路径 + 退出码 1
- 22 个 GitHub 顶层条目（18 文件 + 4 目录）

### Fixed（修复）

- `cli.py:85` 的"报告已保存"提示原用了 `✓`（U+2713）字符，rich 在 Windows GBK 终端抛 `UnicodeEncodeError`，改为纯 ASCII `[OK]`

### Notes（说明）

- 部署模板完全照抄 `omc-replica`（venv + .cmd wrapper + 注册表 PATH 写入）
- 与 `omc-replica` 完全独立，无运行时耦合
- 三个 check 之外的 `permissions` / `transcript` / `disk` 推迟到 v0.2
- v0.4 计划加 MCP server 集成（仿 `omc-replica` 的 mcp_server.py）

---

[0.1.0]: https://github.com/Leon-LI1231/claude-doctor/releases/tag/v0.1.0
