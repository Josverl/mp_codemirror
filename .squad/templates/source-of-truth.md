# Source of Truth Hierarchy

| File | Status | Who May Write | Who May Read |
|------|--------|---------------|--------------|
| `.github/agents/squad.agent.md` | **Authoritative governance.** | Repo maintainer (human) | Squad (Coordinator) |
| `.squad/decisions.md` | **Authoritative decision ledger.** | Squad (Coordinator) — append only | All agents |
| `.squad/team.md` | **Authoritative roster.** | Squad (Coordinator) | All agents |
| `.squad/routing.md` | **Authoritative routing.** | Squad (Coordinator) | Squad (Coordinator) |
| `.squad/ceremonies.md` | **Authoritative ceremony config.** | Squad (Coordinator) | Squad (Coordinator), Facilitator |
| `.squad/casting/policy.json` | **Authoritative casting config.** | Squad (Coordinator) | Squad (Coordinator) |
| `.squad/casting/registry.json` | **Authoritative name registry.** | Squad (Coordinator) | Squad (Coordinator) |
| `.squad/casting/history.json` | **Derived / append-only.** | Squad (Coordinator) — append only | Squad (Coordinator) |
| `.squad/agents/{name}/charter.md` | **Authoritative agent identity.** | Squad (Coordinator) at creation; agent may not self-modify | Coordinator inlines at spawn |
| `.squad/agents/{name}/history.md` | **Derived / append-only.** Personal learnings. | Owning agent (append), Scribe (cross-agent, summarization) | Owning agent only |
| `.squad/agents/{name}/history-archive.md` | **Derived / append-only.** Archived history. | Scribe | Owning agent (read-only) |
| `.squad/orchestration-log/` | **Derived / append-only.** Agent routing evidence. | Scribe | All agents (read-only) |
| `.squad/log/` | **Derived / append-only.** Session logs. | Scribe | All agents (read-only) |
| `.squad/templates/` | **Reference.** Format guides. | Squad (Coordinator) at init | Squad (Coordinator) |
| `.squad/plugins/marketplaces.json` | **Authoritative plugin config.** | Squad CLI | Squad (Coordinator) |

## Rules

1. If `squad.agent.md` and any other file conflict, `squad.agent.md` wins.
2. Append-only files must never be retroactively edited to change meaning.
3. Agents may only write to files listed in their "Who May Write" column.
4. Non-coordinator agents may propose decisions, but only Squad records them in `decisions.md`.
