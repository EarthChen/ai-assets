---
name: llm-wiki
disable-model-invocation: true
description: >-
  Build and maintain a Karpathy-style LLM knowledge base, an Obsidian markdown
  wiki that an agent compiles from raw sources, queries, lints, and corrects
  from human audit feedback.
---

# LLM Wiki — Karpathy Knowledge Base Pattern

> **Experimental skill — iterating.**
> Authored by Lewis Liu (<lylewis@outlook.com>) · Inspired by [Karpathy's llm-wiki Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

## Core idea

Instead of RAG (re-retrieving raw docs on every query), the LLM **compiles** raw sources into a persistent, cross-linked wiki. Every ingest, query, lint, and audit pass makes the wiki richer. Knowledge compounds — and the human stays in the loop via a structured feedback channel instead of ad-hoc corrections that get lost.

- **You** own: sourcing raw material, asking good questions, steering direction, filing feedback on anything the AI got wrong.
- **LLM** owns: all writing, cross-referencing, filing, bookkeeping, and acting on your feedback.

The wiki is a living artifact with **five operations** — `compile`, `ingest`, `query`, `lint`, `audit`. Every session starts by reading `CLAUDE.md` and `wiki/index.md`.

## Directory layout

```
<wiki-root>/
├── CLAUDE.md          ← Schema: scope, conventions, current articles, gaps
├── log/               ← Per-day operation log (one file per day)
│   ├── 20260409.md
│   └── 20260410.md
├── audit/             ← Human feedback inbox (one file per comment)
│   ├── 20260409-143022-claude-code-size.md
│   └── resolved/      ← Processed feedback, archived with resolution notes
├── raw/               ← Immutable source documents (LLM reads, never writes)
│   ├── articles/
│   ├── papers/
│   ├── notes/
│   └── refs/          ← Pointer files for large binaries kept outside raw/
├── wiki/              ← LLM-generated knowledge (LLM writes, you read)
│   ├── index.md       ← Master catalog — every page, structured by category
│   ├── concepts/      ← Concept/topic pages (split into subfolders when >1200 words)
│   ├── entities/      ← People, tools, papers, organizations
│   └── summaries/     ← Per-source summary pages
└── outputs/
    └── queries/       ← Query answers (promote durable ones to wiki/)
```

`CLAUDE.md` is the **schema file** — the single most important configuration. It tells the LLM the wiki's scope, naming conventions, current article list, open questions, and research gaps. Section guide: `references/schema-guide.md`.

## Core principles

Three rules govern everything below. If a future instruction contradicts one, flag it to the user before acting.

1. **Divide and conquer.** Keep each concept page at 400–1200 words; a larger topic becomes a folder `wiki/concepts/<topic>/`. Before writing or splitting any page, read `references/article-guide.md`.
2. **Mermaid for diagrams, KaTeX for formulas.** Syntax: `references/article-guide.md`.
3. **Audit is the human feedback surface.** Humans file corrections as files in `audit/`. Run the `audit` op whenever `audit/*.md` exists; each resolved file moves to `audit/resolved/` with a `# Resolution` section and a log entry. File format: `references/audit-guide.md`.

---

## The five operations

Every action on the wiki is one of these five. Read the matching procedure before acting. Each op appends an entry to the current day's log file (`log/YYYYMMDD.md`). `<skill-dir>` = the directory containing this SKILL.md; scripts run as `uv run <skill-dir>/scripts/<name>.py`.

| Op | Run when | Procedure |
| --- | --- | --- |
| `compile` | after a big ingest batch, a page past 1200 words, a stale `index.md`, or "clean up the wiki" | `references/op-compile.md` |
| `ingest` | the user adds a new source | `references/op-ingest.md` |
| `query` | the user asks a question to answer from the wiki | `references/op-query.md` |
| `lint` | periodic health check | `references/op-lint.md` |
| `audit` | `audit/*.md` feedback files are open | `references/op-audit.md` |

Other references:

- New wiki: `references/new-wiki.md`
- `index.md` layout: `references/index-format.md`
- `log/` format: `references/log-guide.md`
- `CLAUDE.md` sections: `references/schema-guide.md`
- Page templates and writing rules: `references/article-guide.md`
- Audit file format: `references/audit-guide.md`
- Optional tooling (Obsidian, Web Clipper): `references/tooling-tips.md`
