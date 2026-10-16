# CLAUDE.md Schema Guide

`CLAUDE.md` (also read as `AGENTS.md` by some tools) is the **schema document** of a wiki. It tells the LLM the scope, conventions, current state, and open questions. Read it together with `wiki/index.md` at the start of every session. Co-evolve it with the wiki: update it after every compile, ingest batch, or structural change.

**Template source**: `scripts/scaffold.py` writes the template (single source). Edit the template there; this guide only explains how to fill each section.

## Sections

| Section | Fill with | Update when |
| --- | --- | --- |
| Scope | Included areas and deliberate exclusions. A wiki on "LLM memory techniques" excludes "LLM training". | Monthly review |
| Operations | The five ops and the log rule (written by scaffold). | Never |
| Naming conventions | Page-name style per folder; enforce it, because a broken wikilink is an orphan. | When a convention changes |
| Current articles | Every existing page with a one-line summary, so the LLM sees what exists before creating a page (duplicates with slightly different names are the most common error). | After every new concept page |
| Open research questions | Questions that should drive ingest/query work, gaps, contradictions between articles. | After every lint pass; prune stale ones monthly |
| Research gaps | `- [ ]` checklist of sources to ingest. | After every ingest batch |
| Audit backlog | Open-audit counts per target, refreshed from `audit_review.py --open`. Check it at session start to decide whether to run `audit` before ingesting. | After every audit pass |
| Notes for the LLM | Language (zh/en), tone, depth, how to handle contradictions. | As needed |

## Naming examples

- Concept pages: Title Case noun phrases — "Market Making Strategy", not "market making" or "MarketMakingStrategy".
- Entity pages: proper names — "Andrej Karpathy", "Obsidian".
- Summary pages: kebab-case source slug — "karpathy-llm-wiki-gist".
- Page frontmatter fields and templates: [article-guide.md](article-guide.md). Wikilink rules: same file.
