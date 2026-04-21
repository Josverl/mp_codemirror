# Danny — History

## Core Context

- **Project:** A CodeMirror 6 Python editor with PyScript-based LSP server providing MicroPython type checking and completions, needing full test suite rewrite.
- **Role:** Architect
- **Joined:** 2026-04-20T17:05:24.410Z

## Learnings

### 2026-04-21: Test Strategy Review

**Task:** Analyze root causes of slow test failures and propose systemic fixes.

**Key Findings:**
- Root cause #1: `time.sleep()` used for LSP synchronization (8s unconditional waits, 2+ minutes across suite)
- Root cause #2: Cascading timeout multiplication (8s sleep + 20s timeout = 28s per failure)
- Root cause #3: CDN re-fetch on every page load (2-5s per test, 30-75s waste in editor tests)
- Root cause #4: No build-dependency skip guards in spike/transport tests (4-5 min waste)
- Root cause #5: Three separate HTTP servers on different ports (unnecessary complexity)

**Proposed 4-Tier System:**
- Tier 0: Unit (pure Python, <2s) — no browser
- Tier 1: Editor UI (browser + HTTP, <15s) — no LSP
- Tier 2: Worker/Transport (browser + HTTP + dist/worker.js, <30s)
- Tier 3: Full LSP Integration (all above + LSP bridge, <60s)

**Quick Wins (Prioritized):**
1. Add pytest markers (unit, editor, worker, lsp) — 30 min, enables fast loops
2. Add skipif for missing dist/worker.js — 5 min, saves 4-5 min when not built
3. Replace time.sleep(8) with wait_for_function() — 1 hour, saves 75-120s
4. Share HTTP server fixture — 1-2 hours, cleaner architecture
5. Share browser page for Tier 1 tests — 1 hour, saves 20-75s
6. Reduce worker transport timeout from 45s to 15s — 5 min, faster failure detection

**Team Gaps Identified:**
- Need Web Worker / JS testing specialist → **Hired Turk (Vitest, Node.js, webpack, MSW)**
- Need CI/test infrastructure specialist (future hiring)

**Artifacts:**
- .squad/decisions/inbox/danny-test-strategy-review.md — Detailed root cause analysis
- .squad/decisions/inbox/danny-test-strategy.md — 4-tier system, specific recommendations, target test structure

**Decisions Made:** Merged to decisions.md. 4-tier system approved. Turk hired.

