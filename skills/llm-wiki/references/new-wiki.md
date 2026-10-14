# Starting a new wiki

```bash
uv run <skill-dir>/scripts/scaffold.py <wiki-root> "<Topic Title>"
```

Creates the full tree (including `log/<today>.md`, `audit/`, `audit/resolved/`), a blank `CLAUDE.md` based on the new template, and a blank `wiki/index.md` with the recommended category layout.

After scaffolding:

1. Fill in `CLAUDE.md` — define scope, naming conventions, initial research questions.
2. Start ingesting sources.
3. Ask questions to build up `outputs/queries/`; promote durable answers.
4. Run `lint` periodically.
5. Run `audit` whenever new feedback accumulates.
