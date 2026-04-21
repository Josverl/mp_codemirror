# Saul — History

## Project Context
- **Project:** mp_codemirror — CodeMirror 6 editor with Pyright LSP in Web Worker
- **Stack:** HTML5/JS (ES modules via CDN), Python (pytest), webpack, GitHub Pages
- **User:** Jos
- **Branch:** feat/browser-pyright-worker

## Learnings
<!-- Append new learnings below -->

### 2026-04-21: Release Readiness Review
- **Versions:** Both `package.json` and `pyproject.toml` at `0.1.0`. No git tags exist.
- **No CHANGELOG.md** — critical gap. Squad templates expect it for release validation.
- **Deploy not gated on tests** — `deploy.yml` and `test.yml` are independent workflows. Push to main deploys even if tests fail.
- **Deploy pipeline missing stubs** — `pack-stubs` not called, `assets/` not copied to deploy dir. Board switching (RP2, STM32) would be broken in production.
- **4 critical items** block v1.0: changelog, test gating, pack-stubs in deploy, assets copy.
- **Key files:** deploy.yml (lines 1-60), test.yml (lines 1-95), package.json, pyproject.toml, assets/stubs-manifest.json.
- **Branch:** Still on `feat/browser-pyright-worker` — needs merge to main before any release.
