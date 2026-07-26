# Claude Code 使用笔记（个人操作参考，不进模型上下文）

> 原 `rules/common/common-performance.md`。内容是给人看的操作说明（键位、环境变量），模型无法执行，故移出 rules。

## Context Window Management

Avoid last 20% of context window for:
- Large-scale refactoring
- Feature implementation spanning multiple files
- Debugging complex interactions

Lower context sensitivity tasks:
- Single-file edits
- Independent utility creation
- Documentation updates
- Simple bug fixes

## Extended Thinking + Plan Mode

Extended thinking is enabled by default.

Control extended thinking via:
- **Toggle**: Option+T (macOS) / Alt+T (Windows/Linux)
- **Config**: Platform settings (e.g. `alwaysThinkingEnabled`)
- **Budget cap**: `export MAX_THINKING_TOKENS=10000` (bash) or `$env:MAX_THINKING_TOKENS = "10000"` (PowerShell)
- **Verbose mode**: Ctrl+O to see thinking output

For complex tasks requiring deep reasoning:
1. Ensure extended thinking is enabled (on by default)
2. Enable **Plan Mode** for structured approach
3. Use multiple critique rounds for thorough analysis
4. Use split role sub-agents for diverse perspectives

## Build Troubleshooting

If build fails:
1. Use **build-error-resolver** agent
2. Analyze error messages
3. Fix incrementally
4. Verify after each fix
