---
name: code-quality-checklist
description: "Code quality gate — the pre-completion checklist: readable naming, functions <50 lines, files <800, nesting ≤4, error handling, no hardcoded values, no mutation in new code. Use when marking work done, self-reviewing, or in code review."
---

# Code Quality Checklist

## When to Use

Run this gate before marking any task complete — during self-review or code review. It is the final pass that catches the issues a working-but-unfinished change still carries.

## Checklist

Before marking work complete:

- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines)
- [ ] Files are focused (<800 lines)
- [ ] No deep nesting (>4 levels)
- [ ] Proper error handling
- [ ] No hardcoded values (use constants or config)
- [ ] No mutation in new code (immutable patterns used)
