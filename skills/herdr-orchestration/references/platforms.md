# Platform Profiles

The protocol in SKILL.md is platform-neutral; this file is the lookup table for
everything that is not. One profile per herdr agent kind. The herdr binary is
the authority for which kinds exist — run a bare `herdr agent` and check the
`kinds:` line before relying on a kind name.

Defaults (SKILL.md: Constants): worker kind `pi`, thinking level `low` — both
decided per worker at spawn; mixed pools are allowed. A profile's spawn args
are native agent arguments — pass them after `--` on `herdr agent start`.

## pi (default)

- **Spawn**: `herdr agent start <name> --kind pi --pane <pane-id> -- --thinking <level>`
- **Autonomy**: needs none — pi runs tools without approval gates.
- **Thinking**: `--thinking off|minimal|low|medium|high|xhigh|max` at spawn.
  Level change = **warm respawn**:
  `herdr agent start <name> --kind pi --pane <pane-id> -- --session <session-id> --thinking <new-level>`
  — the session restores and the explicit flag overrides the saved level
  (verified pi 0.84.2). Caveat: any level change also persists as pi's
  global `defaultThinkingLevel` setting — harmless here because every spawn
  passes `--thinking` explicitly.
- **Compact**: `/compact <instructions>` — instructions shape the summary only,
  nothing executes afterwards (hence the two-prompt compaction sequence).
- **Auto-compact on overflow**: yes, lossy. Recovery: brief + progress.md +
  state card.
- **Telemetry**: TUI footer renders `ctx <pct>%/<window>` (e.g. `ctx 19.7%/512k`).
  Pattern: `ctx [0-9]+(\.[0-9]+)?%/[0-9]+[kKmM]?`
- **Skill invocation** (brief `execution:` line): `/skill:<name>`
- **Session JSONL** (telemetry escape hatch): the pi session log, latest
  `message.usage.totalTokens`.
- **Session capture**: right after `herdr agent start` returns, record the
  worker's session id — newest `.jsonl` under `~/.pi/agent/sessions/`
  (`PI_CODING_AGENT_SESSION_DIR` overrides) — in the state card; warm
  respawn needs it.

## claude (Claude Code)

- **Spawn**: `herdr agent start <name> --kind claude --pane <pane-id> -- --dangerously-skip-permissions`
- **Autonomy**: `--dangerously-skip-permissions` (≡ `--permission-mode
  bypassPermissions`). Claude cannot enter bypass mid-session — the flag must
  be present at spawn. Trust level equals a pi worker; never point such a
  worker at untrusted content without telling the user.
- **Thinking**: no spawn flag. Thinking is on by default (effort defaults to
  high on current models — expensive). Set the level right after spawn, before
  the first assignment: prompt `/effort <level>` (`low|medium|high|xhigh|max`;
  verify the command exists in that Claude version — if it does not, fall
  back to warm respawn: `claude --resume <session-id>` plus the spawn flag,
  session id = the JSONL filename below). Mid-session re-adjustment works
  the same way while the worker is idle.
- **Compact**: `/compact <instructions>` — focus instructions supported,
  same two-prompt sequence as pi.
- **Auto-compact on overflow**: yes, near ~95% of the window.
- **Telemetry**: the footer shows `N% until auto-compact` only near the
  threshold — a visible indicator means ctx is already high (treat as ≥
  COMPACT_AT, compact at the next boundary); an absent indicator means usage
  sits below that threshold — record and move on. Only an unreadable footer
  is `unknown` (SKILL.md: Telemetry degradation chain).
  Pattern: `[0-9]+% until auto-compact`
- **Skill invocation**: `/<name>` (skills surface as slash commands;
  user-level skills live in `~/.claude/skills/`).
- **Session JSONL** (telemetry escape hatch):
  `~/.claude/projects/<cwd-slug>/<session-id>.jsonl`, latest
  `message.usage.totalTokens`.

## codex (Codex CLI)

- **Spawn**: `herdr agent start <name> --kind codex --pane <pane-id> -- --sandbox workspace-write --ask-for-approval never -c model_reasoning_effort=<level>`
- **Autonomy**: sandbox `workspace-write` + approval `never` — commands that
  exceed the sandbox fail instead of blocking (fail loud; adjust the brief, or
  grant extra dirs with `--add-dir` at spawn). Same trust caveat as claude.
- **Thinking**: `-c model_reasoning_effort=minimal|low|medium|high|xhigh`
  (config override, applies to the whole session). Codex defaults to `medium`.
  Level change = **warm respawn**:
  `herdr agent start <name> --kind codex --pane <pane-id> -- resume <session-id> --sandbox workspace-write --ask-for-approval never -c model_reasoning_effort=<new-level> -C <pane cwd>`
  — `resume` accepts the same global flags; `-C` pins the directory (without
  it codex may prompt on cwd mismatch). The TUI's `/model` picker also
  changes effort but is interactive — unusable unattended.
- **Compact**: `/compact` — takes NO instructions, and Codex asks for
  confirmation before summarizing. Sequence: send `/compact`, wait for
  `blocked`, inspect the dialog (state etiquette), confirm via send-keys,
  then re-anchor from the state card as usual.
- **Auto-compact on overflow**: yes (`model_auto_compact_token_limit`).
- **Telemetry**: footer/status line shows remaining context as `N% left` →
  usage = 100 − N. Pattern: `[0-9]+% left` (footer layout is user-configurable
  via `tui.status_line` — self-heal when the pattern is absent).
- **Skill invocation**: `$<name>` (skills load from `~/.codex/skills/`,
  `.codex/skills/`, and `~/.agents/skills/`).
- **Session JSONL** (telemetry escape hatch): rollout logs under
  `~/.codex/sessions/`, latest `token_count` event.
- **Session capture**: right after spawn, record the worker's session id —
  newest rollout under `~/.codex/sessions/` — in the state card.

## Adding another kind

herdr recognizes more kinds (gemini, cursor, opencode, …). To admit one:
verify spawn args for unattended autonomy, a compaction command (or document
"respawn instead of compact"), a level-change path (in-session command or
session resume — else document cold respawn), a parseable context indicator
(or document "telemetry unavailable → fallback heuristic"), and the
skill-invocation syntax — then write its profile here. Spawn a kind only
after its profile exists here.
