# Virgil — History

## Project Context
- **Project:** mp_codemirror — CodeMirror 6 editor with Pyright LSP in a Web Worker for MicroPython
- **Stack:** HTML5, ES6+ JavaScript, CodeMirror 6 (CDN/esm.sh), Pyright Web Worker, webpack, pytest + Playwright
- **User:** Jos
- **Audience:** Tool developers who build products with CodeMirror, targeting MicroPython users

## Learnings

### 2026-04-21: Architecture Diagrams Created
- Created `docs/architecture.md` with 4 Mermaid diagrams: Component Overview, LSP Communication Flow, Board Switch Flow, Build Pipeline
- Key architecture patterns discovered:
  - Transport factory selects worker (default) or websocket (dev) based on URL params
  - Worker handshake: serverLoaded → initServer (with board stubs) → serverInitialized → LSP init
  - Board switch tears down entire worker and rebuilds (no hot-swap)
  - ESP32 stubs are bundled into worker via arraybuffer-loader; other boards fetched on demand
  - ZenFS mounts: /typeshed-fallback (zip), /typings (board stubs zip), /workspace (in-memory)
  - `fs` aliased to `@zenfs/core` in webpack so Pyright's Node fs calls work in browser
  - SimpleLSPClient handles workspace/configuration requests from Pyright with typeshed/stub paths
  - 300ms debounce on didChange notifications
- Used `classDef` for color-coding diagram layers (UI=blue, editor=green, LSP=purple, worker=red, external=gray)
