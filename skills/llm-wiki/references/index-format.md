# `wiki/index.md` format

The LLM rebuilds `index.md` on every compile and touches it on every ingest. Format:

```markdown
# Index — <Topic>

> One-sentence scope of the wiki.

## 🔖 Navigation
- [[#Concepts]] · [[#Entities]] · [[#Summaries]] · [[#Open Questions]]

## Concepts
### <Category A>
- [[concepts/Foo]] — one-line summary
- [[concepts/Bar/index|Bar]] — (folder-split) one-line summary
    - [[concepts/Bar/aspect-1]] — ...
    - [[concepts/Bar/aspect-2]] — ...

### <Category B>
- ...

## Entities
- [[entities/Andrej Karpathy]] — AI researcher, author of the llm-wiki pattern

## Summaries (chronological)
- 2026-04-09 — [[summaries/llm-wiki-gist]] — Karpathy's original Gist

## Open Questions
- Q1: ...
```

Rules:

- Every wiki page must appear exactly once in `index.md`. `lint` enforces this.
- Folder-split concepts show hierarchy via indented bullets.
- `index.md` + `CLAUDE.md` together are what the AI reads at session start.
