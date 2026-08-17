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
  Level changes are not part of the protocol — respawn the worker under the
  same name instead (state lives in files).
- **Compact**: `/compact <instructions>` — instructions shape the summary only,
  nothing executes afterwards (hence the two-prompt compaction sequence).
- **Auto-compact on overflow**: yes, lossy. Recovery: brief + progress.md +
  state card.
- **Telemetry**: TUI footer renders `ctx <pct>%/<window>` (e.g. `ctx 19.7%/512k`).
  Pattern: `ctx [0-9]+(\.[0-9]+)?%/[0-9]+[kKmM]?`
- **Skill invocation** (brief `execution:` line): `/skill:<name>`
- **Session JSONL** (telemetry escape hatch): the pi session log, latest
  `message.usage.totalTokens`.

## claude (Claude Code)

- **Spawn**: `herdr agent start <name> --kind claude --pane <pane-id> -- --dangerously-skip-permissions`
- **Autonomy**: `--dangerously-skip-permissions` (≡ `--permission-mode
  bypassPermissions`). Claude cannot enter bypass mid-session — the flag must
  be present at spawn. Trust level equals a pi worker; never point such a
  worker at untrusted content without telling the user.
- **Thinking**: no spawn flag. Thinking is on by default (effort defaults to
  high on current models — expensive). Set the level right after spawn, before
  the first assignment: prompt `/effort <level>` (`low|medium|high|xhigh|max`;
  verify the command exists in that Claude version — if it does not, accept
  the default and note it in the ledger). Mid-session re-adjustment works the
  same way while the worker is idle.
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

**Windows caveat (manual starts only).** The `herdr agent start … -- claude …`
form above is resolved by herdr and works as-is. But if you ever launch the
Claude CLI yourself on Windows (e.g. to test or to drive it outside herdr),
`claude` is a `*.cmd` shim, **not** an `.exe`. `Start-Process -FilePath claude`
fails with *"%1 不是有效的 Win32 应用程序"*. Use the call operator instead:

```powershell
& claude --dangerously-skip-permissions          # correct
# NOT: Start-Process -FilePath claude -ArgumentList '--dangerously-skip-permissions' -NoNewWindow -Wait
```

The same applies to `codex` and `herdr` if invoked manually on Windows.

## codex (Codex CLI)

- **Spawn**: `herdr agent start <name> --kind codex --pane <pane-id> -- --sandbox workspace-write --ask-for-approval never -c model_reasoning_effort=<level>`
- **Autonomy**: sandbox `workspace-write` + approval `never` — commands that
  exceed the sandbox fail instead of blocking (fail loud; adjust the brief, or
  grant extra dirs with `--add-dir` at spawn). Same trust caveat as claude.
- **Thinking**: `-c model_reasoning_effort=minimal|low|medium|high|xhigh`
  (config override, applies to the whole session). Codex defaults to `medium`.
  The TUI's `/model` picker also changes effort mid-session, but it is
  interactive — prefer respawning for a level change.
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

## Paths & shell notes (cross-platform)

Several profiles above use POSIX home-directory paths (`~`). On Windows
PowerShell, translate them to `$HOME`:

- `~/.claude/...` → `$HOME\.claude\...`
- `~/.codex/...`   → `$HOME\.codex\...`
- `~/.agents/...`  → `$HOME\.agents\...`

All `herdr` CLI invocations in this file are shell-agnostic (no redirection,
no pipes) and run unchanged on PowerShell. The polling/telemetry loops that
do use shell features live in SKILL.md with both bash and PowerShell forms.

## Adding another kind

herdr recognizes more kinds (gemini, cursor, opencode, …). To admit one:
verify spawn args for unattended autonomy, a compaction command (or document
"respawn instead of compact"), a parseable context indicator (or document
"telemetry unavailable → fallback heuristic"), and the skill-invocation
syntax — then write its profile here. Spawn a kind only after its profile
exists here.
