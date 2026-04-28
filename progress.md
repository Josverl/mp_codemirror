# Multi-File Editor — Implementation Progress

Branch: `copilot/add-multiple-documents-support`

## Goal

Add multi-file support to the CodeMirror Python editor:
- OPFS-backed persistent file storage (with localStorage fallback)
- File tree sidebar (create / rename / delete)
- Tab bar for open files
- Multiple files type-checked together by Pyright in one workspace

---

## Completed

- [x] `src/storage/opfs-project.js` — OPFS storage: writeFile, readFile, listFiles, deleteFile, renameFile, last-active-file persistence, seeds `main.py` on first load
- [x] `src/editor/document-manager.js` — per-file EditorState cache, openFile / saveFile / closeFile, dirty tracking, syncFromView helper
- [x] `src/ui/tab-bar.js` — tab bar with close (×) buttons and dirty (•) indicator
- [x] `src/ui/file-tree.js` — collapsible tree sidebar; New / Rename / Delete actions; keyboard nav
- [x] `src/index.html` — workspace flex layout: file-tree-panel, sidebar-resize-handle, tab-bar, editor-column; Export/Import buttons
- [x] `src/styles.css` — all new component styles (dark/light theme aware)
- [x] `src/app.js` — OPFS init, DocumentManager / TabBar / FileTree wiring, syncFile on edits, sidebar resize, export/import via fflate CDN
- [x] `src/worker/messages.ts` — `MsgSyncFile` type added
- [x] `src/worker/pyright-worker.ts` — `syncFile` handler: writes files to ZenFS `/workspace/` so Pyright sees all open files
- [x] `tests/test_opfs_storage.py` — 7 OPFS storage API tests (**all passing**)
- [x] `tests/test_file_tree.py` — 8 file tree UI tests (**passing**)
- [x] `tests/test_multi_file.py` — 4 multi-document switching tests; `test_edit_preserves_content_on_switch` now passes after fixing the file-tree switch path

---

## Remaining / In Progress

- [ ] Broad regression pass for the multi-file slice — targeted fix is verified locally with `uv run pytest tests/test_multi_file.py -k test_edit_preserves_content_on_switch -v`; related editor tests should be rerun as needed when adjacent multi-file work lands.
- [ ] `dist/pyright_worker.js` rebuild — webpack output is **gitignored**; CI builds it automatically during `worker-tests` job (`npx webpack --mode production`). No local action needed unless you explicitly want a local production bundle check.

---

## Test Commands

```bash
# All editor/UI tests (Playwright)
uv run pytest tests/test_file_tree.py tests/test_opfs_storage.py tests/test_multi_file.py -v

# Only unit tests (no browser)
uv run pytest -m unit -v

# All tests
uv run pytest tests/ -v
```

## Build Commands

```bash
# Install node deps
npm ci --ignore-scripts

# Build Pyright worker (slow, ~5 min, output: dist/pyright_worker.js)
npx webpack --mode production

# Dev build (faster, larger output)
npx webpack --mode development
```

---

## Architecture Notes

- **OPFSProject** is exposed on `window` for Playwright test access (`window.OPFSProject`).
- **DocumentManager** swaps `EditorState` objects; a single `EditorView` is reused.
- `syncFromView()` must be called before every `openFile()` call to flush the current view state into the cache.
- `src/app.js` now does that unconditionally in the file-tree `onOpen` handler before any file switch.
- The Pyright worker receives `{ type: 'syncFile', path, content }` messages to update its ZenFS workspace.
- `dist/` is in `.gitignore`; the webpack build runs in CI.
