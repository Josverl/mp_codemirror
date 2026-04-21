# Yen — History

## Project Context
- **Project:** mp_codemirror — CodeMirror 6 editor with Pyright LSP in Web Worker
- **Stack:** HTML5/JS (ES modules via CDN), Python (pytest), webpack, GitHub Pages
- **User:** Jos
- **Branch:** feat/browser-pyright-worker

## Learnings
<!-- Append new learnings below -->

### 2026-04-21: Initial Security Review Plan
- **No CSP** exists in index.html — highest priority gap. GitHub Pages only supports meta tag CSP (no HTTP headers).
- **No SRI** on CDN imports — import maps don't support integrity attributes (browser limitation). CDN URLs are version-pinned which is good but not tamper-proof.
- **XSS patterns are clean** — hover.js, diagnostics.js, completion.js all use safe DOM APIs (createElement + textContent). No innerHTML with LSP data anywhere in production code.
- **Worker messages** get basic type checks but no schema validation — defense-in-depth opportunity.
- **Supply chain:** pyright pinned to git hash, CDN versions pinned, webpack uses only built-in plugins, `--ignore-scripts` used in deploy. But no `npm audit` in CI and unclear if lockfile is committed.
- **GitHub Actions** pinned to major version tags not SHA hashes.
- **Key files:** src/index.html (CSP target), src/lsp/hover.js (cleanest XSS surface), src/lsp/worker-transport.js (message validation), .github/workflows/deploy.yml (CI security).
- **CSP challenge:** The inline `<script type="importmap">` block requires either `unsafe-inline` or a nonce in script-src, which complicates CSP. Research nonce approach vs. externalizing the import map.
