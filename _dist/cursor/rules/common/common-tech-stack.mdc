---
description: "Tech stack constraints: mandatory uv/pnpm, Python-first scripts, SRP, visualization"
alwaysApply: true
---
# 技术栈约束 (Strict Tech Stack)


## Python 环境管理
- **唯一工具**：必须且仅能使用 `uv`。
- **严禁使用**：禁止使用 `pip`、`conda` 或 `poetry`。
- **标准工作流**：
  - 初始化：`uv venv`
  - 依赖安装：`uv pip install <package>`
  - 脚本执行：`uv run <script>.py`

## Node.js 生态
- **唯一工具**：必须且仅能使用 `pnpm`。
- **严禁使用**：禁止使用 `npm` 或 `yarn`。
- **自动转换**：若用户提供 `npm` 指令，必须自动将其转换为 `pnpm` 等效版本后再执行。

## 代码与架构标准
- **默认脚本**：自动化脚本首选 Python。
- **设计原则**：严格遵守单一职责原则 (SRP)，函数应短小精悍，逻辑原子化。
- **可视化**：复杂逻辑、系统架构或调用链路必须使用 `Mermaid` 或 `PlantUML` 提供可视化图表。
