# Client Compatibility — Full Reference

## Platform Detection

Before spawning agents, determine the platform by checking available tools:

1. **CLI mode** — `task` tool is available → full spawning control. Use `task` with `agent_type`, `mode`, `model`, `description`, `prompt`. Collect results via `read_agent`.
2. **VS Code mode** — `runSubagent` or `agent` tool is available → conditional behavior. Use `runSubagent` with prompt only. Drop `agent_type`, `mode`, `model`, `description`. Multiple subagents in one turn run concurrently. Results return automatically.
3. **Fallback mode** — neither available → work inline. Do not apologize.

If both `task` and `runSubagent` are available, prefer `task`.

## VS Code Spawn Adaptations

- **Spawning tool:** Use `runSubagent`. Prompt is the only required parameter.
- **Parallelism:** Spawn ALL concurrent agents in a SINGLE turn. They run in parallel automatically.
- **Model selection:** Accept the session model. Do NOT attempt per-spawn model selection or fallback chains.
- **Scribe:** Cannot fire-and-forget. Batch Scribe as the LAST subagent in any parallel group.
- **Launch table:** Skip it. Results arrive with the response.
- **`read_agent`:** Skip entirely. Results return automatically.
- **`agent_type`:** Drop it. All VS Code subagents inherit parent's tools.
- **`description`:** Drop it. Agent name is already in the prompt.
- **Prompt content:** Keep ALL prompt structure — charter, identity, task, hygiene, response order.

## Feature Degradation Table

| Feature | CLI | VS Code | Degradation |
|---------|-----|---------|-------------|
| Parallel fan-out | `mode: "background"` + `read_agent` | Multiple subagents in one turn | None — equivalent concurrency |
| Model selection | Per-spawn `model` param | Session model only | Accept session model, log intent |
| Scribe fire-and-forget | Background, never read | Sync, must wait | Batch with last parallel group |
| Launch table UX | Show table → results later | Skip table → results with response | UX only |
| SQL tool | Available | Not available | Use filesystem-based state |
| Response order bug | Critical workaround | Possibly necessary | Keep the block — harmless if unnecessary |

## SQL Tool Caveat

The `sql` tool is **CLI-only**. Cross-platform code paths must not depend on SQL. Use filesystem-based state (`.squad/` files) for anything that must work everywhere.
