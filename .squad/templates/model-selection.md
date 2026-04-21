# Per-Agent Model Selection — Full Reference

## Layer Hierarchy (first match wins)

### Layer 0 — Persistent Config (`.squad/config.json`)

On session start, read `.squad/config.json`:
- `agentModelOverrides.{agentName}` → use that model for this specific agent
- `defaultModel` → use for ALL agents
- Survives across sessions

**User commands:**
- "always use X" / "default to X" → write `defaultModel` to config.json
- "use X for {agent}" → write to `agentModelOverrides.{agent}`
- "switch back to automatic" → remove `defaultModel` from config.json

### Layer 1 — Session Directive
User specified a model for this session? Use that model until session ends or contradicted.

### Layer 2 — Charter Preference
Agent's charter has `## Model` section with `Preferred` set to a specific model (not `auto`)? Use it.

### Layer 3 — Task-Aware Auto-Selection

Governing principle: **cost first, unless code is being written.**

| Task Output | Model | Tier |
|-------------|-------|------|
| Writing code (implementation, refactoring, test code, bug fixes) | `claude-sonnet-4.5` | Standard |
| Writing prompts or agent designs | `claude-sonnet-4.5` | Standard |
| NOT writing code (docs, planning, triage, logs, mechanical ops) | `claude-haiku-4.5` | Fast |
| Visual/design work requiring image analysis | `claude-opus-4.5` | Premium |

### Layer 4 — Default
`claude-haiku-4.5`. Cost wins when in doubt, unless code is being produced.

## Role-to-Model Mapping

| Role | Default Model | Override When |
|------|--------------|---------------|
| Core Dev / Backend / Frontend | `claude-sonnet-4.5` | Heavy code gen → `gpt-5.2-codex` |
| Tester / QA | `claude-sonnet-4.5` | Simple scaffolding → `claude-haiku-4.5` |
| Lead / Architect | auto (per-task) | Architecture → premium; triage → haiku |
| Prompt Engineer | auto (per-task) | Prompt design → sonnet; research → haiku |
| Copilot SDK Expert | `claude-sonnet-4.5` | Pure research → `claude-haiku-4.5` |
| Designer / Visual | `claude-opus-4.5` | Never downgrade (vision required) |
| DevRel / Writer | `claude-haiku-4.5` | — |
| Scribe / Logger | `claude-haiku-4.5` | Never bump |
| Git / Release | `claude-haiku-4.5` | Never bump |

## Task Complexity Adjustments (apply at most ONE)

- **Bump UP to premium:** architecture proposals, reviewer gates, security audits, multi-agent coordination
- **Bump DOWN to fast:** typo fixes, renames, boilerplate, scaffolding, changelogs
- **Switch to `gpt-5.2-codex`:** large multi-file refactors, heavy code gen (500+ lines)
- **Switch to `gemini-3-pro-preview`:** code/security/architecture reviews after a rejection

## Fallback Chains

Silently retry with next in chain. Max 3 retries before nuclear fallback. Do NOT tell user.

```
Premium:  claude-opus-4.6 → claude-opus-4.6-fast → claude-opus-4.5 → claude-sonnet-4.5 → (omit model param)
Standard: claude-sonnet-4.5 → gpt-5.2-codex → claude-sonnet-4 → gpt-5.2 → (omit model param)
Fast:     claude-haiku-4.5 → gpt-5.1-codex-mini → gpt-4.1 → gpt-5-mini → (omit model param)
```

`(omit model param)` = nuclear fallback, always works.

**Rules:**
- User specified a provider → fall back within that provider first
- Never fall back UP in tier
- Log fallbacks to orchestration log, never surface to user

## Passing Model to Spawns

Only set `model` param when it differs from platform default (`claude-sonnet-4.5`). If nuclear fallback, omit entirely.

**Spawn output format:**
```
🔧 Fenster (claude-sonnet-4.5) — refactoring auth module
📋 Scribe (claude-haiku-4.5 · fast) — logging session
⚡ Keaton (claude-opus-4.6 · bumped for architecture) — reviewing proposal
```
Include tier annotation only when bumped or specialist chosen.

## Valid Models

Premium: `claude-opus-4.6`, `claude-opus-4.6-fast`, `claude-opus-4.5`
Standard: `claude-sonnet-4.5`, `claude-sonnet-4`, `gpt-5.2-codex`, `gpt-5.2`, `gpt-5.1-codex-max`, `gpt-5.1-codex`, `gpt-5.1`, `gpt-5`, `gemini-3-pro-preview`
Fast/Cheap: `claude-haiku-4.5`, `gpt-5.1-codex-mini`, `gpt-5-mini`, `gpt-4.1`
