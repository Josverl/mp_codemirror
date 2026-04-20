# Squad Decisions

## Test Strategy & Architecture (2026-04-21)

### 1. Adopt 4-Tier Test System

The test suite will be reorganized into 4 tiers with progressive infrastructure requirements:

- **Tier 0: Unit Tests** (pure Python, <2s total) — No browser, no server
- **Tier 1: Editor UI Tests** (browser + HTTP, <15s total) — CodeMirror rendering, theme toggle, sample loading, no LSP
- **Tier 2: Worker/Transport Tests** (browser + HTTP + dist/worker.js, <30s total) — Web Worker protocol, transport layer, spike tests, smoke tests (non-LSP)
- **Tier 3: Full LSP Integration** (all above + LSP bridge on :9011, <60s total) — Diagnostics, completions, hover, real-time features

**Rationale:** Current test structure lacks categorization. Tests are grouped by file, not by infrastructure dependency. Many tests fail when dependencies are missing, without proper skip guards. Tier system enables fast feedback loops (run Tier 1 tests in CI on every push, Tier 3 on schedule) and clear dependencies.

**Status:** Approved. See Danny's test-strategy.md for full implementation structure.

---

### 2. Root Causes of Slow Test Failures (Systemic Issues)

Identified and quantified five systemic causes of test slowness:

1. **`time.sleep()` as synchronization** — 8-second unconditional sleeps in LSP init routines (single biggest contributor)
   - Impact: 2+ minutes of pure sleep across ~15 LSP tests before assertions run
   - Solution: Replace with `page.wait_for_function("() => window.__lspReady === true", timeout=15000)`

2. **Cascading timeout multiplication** — Sleep + assertion timeout compounds failures
   - Example: 8s sleep + 20s timeout = 28s per failure, 45s total timeout in worker transport tests
   - Solution: Reduce to reasonable per-test limits (10-15s)

3. **Redundant page loads and CDN fetches** — Every test calls `page.goto()`, reloading all CodeMirror modules from esm.sh
   - Impact: 2-5s per page load × 15+ tests = 30-75s in editor tests alone
   - Solution: Use module-scoped page fixture for read-only tests, share browser context

4. **No build-dependency gating** — `test_spike_worker.py` and `test_worker_transport.py` lack skipif guards for `dist/worker.js`
   - Impact: 6 tests × 15-45s timeout = 4-5 minutes wasted when bundle doesn't exist
   - Solution: Add module-level pytestmark with skipif condition

5. **Port collision and server proliferation** — Three separate HTTP servers on ports 8888, 8889, 8890
   - Impact: Multiple server startup costs, unclear fixture scope
   - Solution: Consolidate to single session-scoped fixture serving from project root

**Status:** Documented. See Danny's test-strategy-review.md and Basher's test-analysis.md for detailed analysis.

---

### 3. Quick Wins (High Impact, Low Effort)

Priority order for implementation:

1. **Add pytest markers** (immediate) — Add markers to `pyproject.toml`: `unit`, `editor`, `worker`, `lsp`
   - Effort: 30 minutes
   - Savings: Enables fast loops (`pytest -m unit`, `pytest -m "not lsp"`)

2. **Add skipif guards to spike/transport tests** (immediate) — Module-level skipif for missing `dist/worker.js`
   - Effort: 5 minutes
   - Savings: 4-5 minutes when bundle not built

3. **Replace `time.sleep(8)` with `wait_for_function()`** (high priority) — Requires app.js change to set `window.__lspReady`
   - Effort: 1 hour (including app.js + tests)
   - Savings: 75-120 seconds across LSP test suite

4. **Share HTTP server fixture** (moderate) — Consolidate conftest.py servers
   - Effort: 1-2 hours
   - Savings: Cleaner architecture, eliminates port collision confusion

5. **Share browser page for read-only editor tests** (moderate) — Module-scoped page for Tier 1 tests
   - Effort: 1 hour
   - Savings: 20-75 seconds in editor tests via eliminated CDN reloads

6. **Reduce worker transport timeout** — Change from 45s to 15s default
   - Effort: 5 minutes
   - Savings: Faster failure detection when worker is broken

---

### 4. Team Gaps Identified

**Gap 1: No Web Worker / JS Testing Specialist**

The spike and transport tests embed large JavaScript blobs inside `page.evaluate()`. This pattern makes debugging hard (errors are opaque strings) and prevents use of JS-native debuggers. No agent has Vitest/Jest expertise.

**Decision:** Hire Turk as **Web/JS Tester** with expertise in Vitest, Node.js, Web Workers, webpack, and MSW (Mock Service Worker).

**Turk's Scope:** JS/TS unit tests, Worker protocol testing (native Node.js, not Playwright), webpack build verification, network mocking, JS-side test infrastructure.

**Status:** ✅ Hired. Charter and history initialized.

---

**Gap 2: No CI/Test Infrastructure Specialist**

Test suite lacks pytest configuration for markers, no parallel execution setup, no build-step gating. Scattered server fixtures across multiple files.

**Recommendation:** (Future) Hire a DevOps/Test Infrastructure specialist (or delegate to Livingston) to set up CI matrix, shared fixtures module, build verification steps.

---

### 5. LSP Test Timing: Completion Debounce Race (Linus, 2025-04-20)

**Decision:** LSP completion requests must be triggered via **Ctrl+Space (explicit)** after waiting for Pyright's `publishDiagnostics` — not via auto-complete on dot-typing.

**Rationale:** CodeMirror fires completion immediately on `.` keystroke (before 300 ms debounce flushes `didChange`). Pyright receives completion request for content it hasn't seen yet, returns `{items: [], isIncomplete: true}`.

**Reliable Test Pattern:**
1. Type full expression (e.g., `sys.arg`)
2. Poll console for `"Received diagnostics"` — proves Pyright has content
3. Press Ctrl+Space to trigger explicit completion

**Implications:** app.js has latent UX bug: auto-completions on `.` will be empty until debounce fires. Out of scope for testing but noted for future frontend work.

**Status:** Documented. Tests using this pattern confirmed reliable.

---

### 6. LSP Bridge Testing Approach (Rusty, 2025-07-22)

**Decision:** Backend LSP bridge tests live in `tests/test_lsp_bridge.py` and test the WebSocket protocol directly — not through the browser.

**Rationale:**
- Node.js bridge runs on `ws://localhost:9011/lsp`, speaks JSON-RPC 2.0 over WebSocket
- `websockets.sync.client` is sufficient — no pytest-asyncio needed
- Direct protocol testing is faster and deterministic than browser E2E tests with `time.sleep()`

**Coverage (20 tests):**
- **Unit (5):** `PyrightBridge` Python class — instantiation, Content-Length header format, unicode byte counting, safe teardown
- **Connection (4):** Port open, WS handshake, wrong-path behavior, concurrent connections
- **Protocol (6):** Initialize result, jsonrpc 2.0, Pyright version log, initialized notification, textDocumentSync capability, shutdown request
- **Diagnostics (5):** didOpen triggers publishDiagnostics, range+message, clean code = no errors, didChange updates diagnostics, URI matches document

**Skip Behavior:** Integration tests skip when bridge not running (requires port 9011 open and server responding).

**Status:** All 20 tests passing. Approach validated.

---

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
