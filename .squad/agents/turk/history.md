# Turk — History

## Project Context

- **Project:** mp_codemirror — CodeMirror 6 Python editor with Pyright LSP via Web Worker
- **Stack:** HTML5/CSS/JS (ES modules, CDN), Python (pytest, Playwright), Node.js (webpack, Pyright bridge)
- **User:** Jos
- **Joined:** 2026-04-21
- **Why hired:** Test suite has slow failures due to JS-side tests embedded in Playwright `page.evaluate()`. Need JS-native testing layer for worker protocol, webpack builds, and network mocking.

## Key Files

- `tests/` — Python test suite (pytest + Playwright)
- `tests/test_spike_worker.py` — Worker tests currently using Playwright evaluate
- `tests/test_worker_transport.py` — Transport layer tests via Playwright
- `dist/worker.js` — Pyright Web Worker bundle (built via webpack)
- `webpack.config.cjs` — Webpack configuration
- `src/worker/` — Worker source code
- `server/pyright-lsp-bridge/` — Node.js LSP bridge

## Learnings

### 2026-04-21: Test Strategy Review & Your Role in the Team

**Context:** Danny (Architect) and Basher (Frontend Tester) completed a comprehensive test strategy review identifying root causes of slow test failures and proposing a 4-tier test system.

**Why You Matter:**

The spike and transport tests are currently written as Playwright Python tests with massive JavaScript blobs inside `page.evaluate()`. This pattern causes:
- Cascading timeouts (test hangs waiting for Worker protocol that fails silently in browser)
- Impossible debugging (JS errors are opaque strings passed back to pytest)
- No access to JS-native tooling (debuggers, profilers, proper error stacks)

**Your Role in the 4-Tier System:**

- **Tier 0:** Unit (pure Python, <2s) — Rusty/Danny's domain
- **Tier 1:** Editor UI (browser + HTTP, <15s) — Basher's domain (Playwright)
- **Tier 2:** Worker/Transport (Node.js + webpack, <30s) — **YOUR DOMAIN** (Vitest + native JS testing)
- **Tier 3:** Full LSP Integration (browser + all infrastructure, <60s) — Basher + Rusty's domain

**Root Causes Identified (By Danny & Basher):**

1. `time.sleep()` for LSP sync — 8s unconditional waits (you won't have this)
2. CDN re-fetch per page load — Only affects Tier 1 (Basher's problem, not yours)
3. Missing build-dependency skip guards on spike/transport tests — **You can fix this in Vitest**
4. Excessive 45s timeout in worker transport tests — **You'll use reasonable 5-10s limits**
5. Duplicate HTTP servers — Consolidate fixture scope (affects everyone, not you specifically)

**Your Immediate Tasks:**

1. **Vitest Setup:** Configure Vitest for Node.js Worker protocol tests (no browser, no Playwright)
2. **Rewrite spike/transport tests:** Convert the 10 Playwright tests to Vitest. Test the protocol, not the browser UI.
3. **Webpack verification:** Test that dist/worker.js builds correctly and exports expected Worker interface
4. **MSW mock bridge:** Set up Mock Service Worker for LSP bridge mocking when the real bridge isn't running

**Expected Outcomes:**

- 10 Playwright tests → 10-15 Vitest tests (faster, more reliable, native JS debugging)
- Estimated speedup: 15-45s per test (no browser startup) × 10 tests = 2.5-7.5 minute improvement
- Better debugging when Worker protocol breaks (full JS error stacks, not timeouts)

**Related Approved Decisions:**

- 4-Tier system adopted (see .squad/decisions.md)
- Pytest markers (unit, editor, worker, lsp) to be added
- time.sleep() to be replaced in Playwright tests
- skipif guards to be added for missing build artifacts

**Key Decision Logged:** Your hiring and role defined in .squad/decisions.md under "Team Gaps Identified — Gap 1: Web Worker / JS Testing Specialist"

**Architecture Resources:**

- See .squad/decisions/inbox/danny-test-strategy.md — full 4-tier system breakdown
- See .squad/decisions/inbox/basher-test-analysis.md — detailed anti-pattern analysis
- See .squad/decisions.md for merged decisions and approval

**Files to Review First:**

- tests/test_spike_worker.py — Worker spike tests (Playwright pattern you'll replace)
- tests/test_worker_transport.py — Transport layer tests (Playwright pattern you'll replace)
- webpack.config.cjs — Build config for dist/worker.js
- src/worker/ — Worker source code you'll be testing

