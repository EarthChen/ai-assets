# Audit Guide — human feedback on wiki content

The `audit/` directory is the human feedback surface. One file per feedback, YAML frontmatter + markdown body. Feedback is filed by humans (an Obsidian plugin, a web viewer, or by hand) and **consumed by the AI during the `audit` operation**.

## Why it exists

AI-written content is wrong sometimes. Raw sources contradict each other. Feedback in chat is lost the moment the conversation ends. The audit directory gives corrections a permanent, location-anchored home that every tool (AI, lint script, audit_review script) understands.

## Directory layout

```
<wiki-root>/audit/
├── 20260409-143022-claude-code-size.md    ← open feedback
├── 20260409-150110-rag-definition.md      ← open feedback
└── resolved/
    ├── 20260408-110505-typo-gemma.md      ← processed, with resolution
    └── 20260407-180012-rejected-scope.md  ← rejected, with rationale
```

- `audit/*.md` — open feedback, not yet processed.
- `audit/resolved/*.md` — processed feedback. Nothing ever gets deleted; rejections stay with their rationale.

## File format

Filename: `YYYYMMDD-HHMMSS-<short-slug>.md`. The prefix is the creation timestamp (local time); the slug is a human-readable hint derived from the selected text or the comment.

```markdown
---
id: 20260409-143022-a1b2
target: tech/Claude_Code.md
target_lines: [45, 52]
anchor_before: "## 技术概览\n\n| 维度 | 详情 |\n|------|------|\n"
anchor_text: "| **规模** | ~1,900 个文件，512,000+ 行代码 |"
anchor_after: "\n| **语言** | TypeScript（strict 模式） |"
severity: warn
author: lewis
source: obsidian-plugin
created: 2026-04-09T14:30:22+08:00
status: open
---

# Comment

实际应该是 ~1,800 个文件，参考 2026-03-31 commit abc123 的 tree。
`find . -type f | wc -l` 当时是 1817。这个数字直接影响下面几个估算。

# Resolution

<!-- Filled in when the audit is processed and moved to resolved/ -->
```

### Frontmatter fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Unique id: `YYYYMMDD-HHMMSS-<4hex>`. Must match filename prefix. |
| `target` | string | yes | Path relative to wiki root. Must be a file that exists (lint check). |
| `target_lines` | `[int, int]` | yes | Best-effort 1-indexed inclusive line range at the time of writing. May drift. |
| `anchor_before` | string | yes | Up to ~80 chars of text immediately before the selection. Verbatim, preserves newlines. |
| `anchor_text` | string | yes | The exact selected text. Verbatim. |
| `anchor_after` | string | yes | Up to ~80 chars of text immediately after the selection. Verbatim. |
| `severity` | enum | yes | One of `info`, `suggest`, `warn`, `error`. |
| `author` | string | yes | Free text. |
| `source` | enum | yes | One of `obsidian-plugin`, `web-viewer`, `manual`. |
| `created` | ISO 8601 | yes | Timestamp with timezone. |
| `status` | enum | yes | `open` for files in `audit/`, `resolved` for files in `audit/resolved/`. |

### Severity semantics

- **info** — "worth noting but not wrong". Example: additional context, alternate phrasing.
- **suggest** — "consider this". Example: reword, reorganize.
- **warn** — "something looks off". Example: stale number, ambiguous sentence.
- **error** — "this is wrong". Example: factual mistake, broken link, wrong attribution.

## Anchor strategy

Line numbers alone are fragile — any edit earlier in the file invalidates them. So every audit file carries a **text-based anchor window** alongside the line numbers.

On read (AI during `audit`, `audit_review.py`):
1. Try `target_lines` — check whether the text in that line range contains `anchor_text`.
2. If not, search the whole file for `anchor_text`. If exactly one match, use it.
3. If multiple matches, use `anchor_before + anchor_text + anchor_after` as a combined search key.
4. If still no match, the anchor is **stale** — flag to the user during the `audit` op. Do not silently drop; ask whether to re-anchor, reject, or archive.

## Processing

The `audit` procedure, the `# Resolution` format, and the status flip live in [op-audit.md](op-audit.md).
