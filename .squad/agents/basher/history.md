# Basher — History

## Core Context

- **Project:** A CodeMirror 6 Python editor with PyScript-based LSP server providing MicroPython type checking and completions, needing full test suite rewrite.
- **Role:** Frontend Tester
- **Joined:** 2026-04-20T17:05:24.413Z

## Learnings

### 2026-04-21: Test Suite Anti-Pattern Analysis

**Task:** Analyze Playwright test patterns and validate Danny's root cause findings.

**Confirmed Anti-Patterns:**
1. `time.sleep()` waste: ~24-40s hardcoded waits per LSP test file (repeated per test)
2. Page reload per test: CDN re-download, 2-5s per test (15+ tests = 30-75s)
3. Missing build checks: test_spike_worker.py and test_worker_transport.py have no skipif guard for dist/worker.js
4. Excessive timeouts: test_worker_transport.py uses 45s default timeout
5. Duplicate server infrastructure: Three separate HTTP servers on ports 8888, 8889, 8890

**Impact Quantification:**
- Missing dist/worker.js skip: 4-5 minutes wasted (6 tests × 15-45s timeout)
- time.sleep(8) LSP waits: 75-120 seconds (5-8s per test × ~15 LSP tests)
- Page reload overhead: 20-75 seconds in test_editor.py alone (10-15 page loads × 2-5s each)

**Test Classification (3 Tiers):**
- Tier 1 (Fast): Editor, CDN, unit tests — <30s total
- Tier 2 (Medium): Spike/transport, smoke tests, full feature tests — needs dist/worker.js
- Tier 3 (Slow): Full LSP integration — needs all infrastructure

**Recommended Fixes (Priority Order):**
1. Add skipif guards to spike/transport tests — 5 min effort, 4-5 min savings
2. Replace time.sleep() with wait_for_function() — 1 hour effort, 75-120s savings
3. Reduce worker transport timeout from 45s to 15s — 5 min effort
4. Share HTTP server fixture — 1-2 hours effort
5. Share browser page for read-only tests — 1 hour effort

**Artifacts:**
- .squad/decisions/inbox/basher-test-analysis.md — Detailed anti-pattern analysis, specific fix recommendations, test classification

**Decision:** Validated Danny's findings. Recommend Turk (new Web/JS Tester) for Vitest + Node.js test layer.

