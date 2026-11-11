# Model and Effort Selection

## Subagent and workflow models

Set `model` on every Agent / workflow `agent()` call by the kind of work:

- `haiku`: work where a mistake is cheap to spot. Find files, read logs, run tests, summarize, classify, extract.
- `sonnet`: well-scoped work against a clear spec. Repeated investigation, review, or drafting tasks. Bulk workers under a lead model.
- Session model (omit `model`): code edits, judgment calls, architecture, review verdicts.
- `fable`: major refactors or migrations, architecture planning, deep research, leading many subagents.

Built-in agents such as Explore inherit the session model. Set `model` on them too.

A migration or a performance optimization stays on the session model or higher, even against a clear spec.

## When the result falls short

Take these steps in order. Stop at the first one that works.

1. Give the work a self-check: a test, a build, or a script that calls the endpoint.
2. Raise effort one level, up to `high`.
3. Move to the next model up, at a lower effort than the smaller model used. After `high`, that is `medium`.

When outcomes are checkable automatically, run everything at `low` effort and re-run only the failures at `high`.

## Session model switch

When the task does not fit the session model, recommend a switch to the user in one line. The user makes the switch.

- Up to `fable`: the `fable` work above, scientific or quantitative analysis, long unattended runs, or `opus` at `high` still falls short.
- Down to `sonnet`: well-scoped bug fix, feature against a spec, everyday documents, interactive chat.

Recommend the switch at a natural break, with `/compact` first. The prompt cache belongs to the model that wrote it: a move down a tier, or any move away from `fable`, drops the earlier reasoning.

## Delegation

Keep the main context for decisions. Send verbose reading (logs, search sweeps, large files) to a cheaper subagent that returns a summary.

Use a lead with parallel cheaper workers only when the work is larger than one context window. Use one agent loop for a chain of dependent steps or for work that fits in one context window.
