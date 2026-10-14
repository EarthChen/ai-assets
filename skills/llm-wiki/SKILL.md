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

`CLAUDE.md` is the **schema file** — the single most important configuration. It tells the LLM the wiki's scope, naming conventions, current article list, open questions, and research gaps. Read `references/schema-guide.md` for what to put in it. Read it at the start of every session.

## Core principles

Four rules govern everything below. If a future instruction contradicts one, flag it to the user before acting.

### 1. Divide and conquer

Keep each concept page at **400–1200 words**. A topic that would exceed that becomes a folder `wiki/concepts/<topic>/`: a short `index.md` (definition, sub-page list) plus one file per aspect, shown as indented bullets in `wiki/index.md`. Split procedure and examples: `references/article-guide.md`.

### 2. Mermaid for diagrams, KaTeX for formulas

Write every flow, sequence, hierarchy, or state diagram in mermaid and every formula in KaTeX (`$...$` inline, `$$...$$` block). Syntax and examples: `references/article-guide.md`.

### 3. Raw file policy

Small text-based sources (md, txt, small pdfs, small images) → copy into `raw/<subfolder>/`.

Large binaries (videos, model weights, installers, datasets, large PDFs >10 MB) → **do not copy**. Instead:

- Create a pointer file at `raw/refs/<slug>.md` with:

  ```yaml
  ---
  kind: ref
  external_path: /Volumes/external/models/llama-3-70b/
  size: ~140 GB
  ---
  ```

  followed by a short description of what it is and why it matters to this wiki.
- Wiki pages cite `[[raw/refs/<slug>]]` exactly like any other source.

This keeps the wiki repo git-friendly and portable.

### 4. Audit is the human feedback surface

The wiki is AI-written; it will be wrong sometimes. The raw sources are human-written; they will contradict each other. The `audit/` directory is how humans correct both without losing the corrections in chat history.

- Humans file feedback via the Obsidian plugin or the web viewer. Each feedback is one file in `audit/` with YAML frontmatter (anchor, target, severity) and a markdown body.
- The AI **must** periodically run the `audit` op — never silently ignore `audit/*.md` files.
- When feedback is applied, the file moves to `audit/resolved/` with a `# Resolution` section appended and a log entry recorded in `log/YYYYMMDD.md`.

See `references/audit-guide.md` for the full file format and processing workflow.

---

## The five operations

Every action on the wiki is one of these five. Read the matching procedure before acting; each appends an entry to the current day's log file (`log/YYYYMMDD.md`).

| Op | Run when | Procedure |
| --- | --- | --- |
| `compile` | after a big ingest batch, a page past 1200 words, a stale `index.md`, or "clean up the wiki" | `references/op-compile.md` |
| `ingest` | the user adds a new source | `references/op-ingest.md` |
| `query` | the user asks a question to answer from the wiki | `references/op-query.md` |
| `lint` | periodic health check | `references/op-lint.md` |
| `audit` | `audit/*.md` feedback files are open | `references/op-audit.md` |

New wiki: `references/new-wiki.md`. `index.md` layout: `references/index-format.md`. Tools and scripts: `references/tooling-tips.md`: Tools overview.

## `log/` format

See `references/log-guide.md` — file naming, entry format, allowed ops, and grep recipes.

## References

- `references/schema-guide.md` — What to put in `CLAUDE.md`
- `references/article-guide.md` — How to write good wiki articles (length, wikilinks, mermaid, math, divide-and-conquer)
- `references/log-guide.md` — The `log/` folder convention
- `references/audit-guide.md` — Audit file format, anchor strategy, processing workflow
- `references/tooling-tips.md` — Tools overview, Obsidian setup, Web Clipper, qmd, plugin + web installation
