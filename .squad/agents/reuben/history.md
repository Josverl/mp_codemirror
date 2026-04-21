# Reuben — History

## Project Context
- **Project:** mp_codemirror — CodeMirror 6 editor with Pyright LSP in Web Worker
- **Stack:** HTML5/JS (ES modules via CDN), Python (pytest), webpack, GitHub Pages
- **User:** Jos
- **Branch:** feat/browser-pyright-worker

## Learnings
<!-- Append new learnings below -->

### 2026-04-21: Initial Code Review Assessment
- **Architecture is solid**: Clean module separation in src/lsp/ — protocol, transport, CM integration are well-decoupled. Transport factory pattern works well.
- **Board switching lifecycle is clean**: Compartment-based reconfiguration with proper teardown/rebuild.
- **Key issue — theme toggle broken**: darkTheme/lightTheme CM extensions defined but never applied. Only CSS body class toggles. Needs Compartment like LSP uses.
- **Protocol violation**: `disconnect()` sends `shutdown` as notification; LSP spec requires it as a request.
- **Pending requests leak**: No cleanup of `pendingRequests` map on disconnect — in-flight requests hang until timeout.
- **Accessibility gaps**: No skip-to-content link, no `prefers-color-scheme` support, hover tooltips mouse-only.
- **Performance opportunity**: LSP modules eagerly imported; could lazy-load after editor renders.
- **Verbose logging**: Heavy console.log throughout LSP modules; needs log-level gating for production.
- **Resilience gap**: No worker crash recovery — user must refresh page if Pyright worker dies.

### 2026-04-21: Documentation Peer Review
- Reviewed all 12 user-facing docs. Found widespread staleness — many files still describe WebSocket-only architecture.
- `PYRIGHT_LSP_PLAN.md` is the worst offender: autocompletion/hover marked as TODO when both are DONE, architecture diagram ignores Web Worker.
- `README.md` roadmap at bottom contradicts feature list at top. CDN version numbers stale.
- `CONTRIBUTING.md` setup instructions outdated (wrong port, missing `uv`, missing worker build step, references `test.html`).
- `server/README.md` and `tests/README.md` use PowerShell syntax on a Linux project.
- Recommended archiving: `CDN_TEST_REPORT.md`, `PYRIGHT_LSP_PLAN.md`, `JESSE_AI_WINDOWS_ISSUE.md` → `.ai_history/`.
- Pattern: docs lag code by 2+ phases. Need a docs-update checklist in PR template.
