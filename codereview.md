# Code Review — `copilot/add-multiple-documents-support`

## Summary of changes
Five Pyright/LSP fixes plus the Stage 1‑5 multi-file UX (OPFS storage, DocumentManager, FileTree, TabBar, workspace sync, share/import-export). Net: +2.1k lines across 20 files. The branch is functionally correct for the verified scenarios; concerns below are mostly architectural / robustness, not correctness blockers.

---

## Strengths

- **Clean separation of concerns**: opfs-project.js (persistence) / document-manager.js (state) / tab-bar.js + file-tree.js (presentation). Each module is independently testable.
- **OPFS + localStorage fallback** keeps the app working in private mode / older Safari.
- **Pyright fixes are well-targeted**: relative paths in `pyrightconfig.json` (31a23c8), `syncFile/deleteFile` interception after `BrowserMessageReader` hijacks `ctx.onmessage` (11302d1, pyright-worker.ts), and the now-corrected `extraPaths: [".", "libs"]` policy.
- **`syncFile` worker message** is the right shape — small, idempotent, keyed by relative path.
- **Tests** for OPFS, file tree, multi-file scenarios are included (although see gaps below).

---

## Issues

### High

1. **Single `EditorView`, state-swapped per tab** is fragile. document-manager.js does:
   - `shouldAdoptExistingViewState` heuristic compares doc text to decide whether to reuse state — easy to break by trivial changes (e.g. clearBtn) before the cache is seeded.
   - Manual `syncFromView()` must be called before every tab switch. Missing it once silently loses keystrokes.
   - Manual `requestAnimationFrame` scroll restore is racy with LSP reconfigures.
   - `rebindLSP()` reconfigures the LSP compartment on every switch — rebuilds the entire extension graph.

   ViperIDE uses **one `EditorView` per tab pane** (editor.js:343, editor_tabs.js:50-51). Each pane element gets its own view, freely preserving undo history, selection, scroll, and lint state without bookkeeping. Consider porting that model in stage 5.
   **Status: Completed - no further action needed.**

2. **No dirty-guard on close.** `tabBar.onClose` calls `docManager.closeFile`, which silently auto-saves. There's no "discard / save / cancel" prompt. ViperIDE asks (editor_tabs.js:131-134). Auto-save is reasonable but should be a deliberate choice and documented; today it's implicit.
   **Status: Completed - no further action needed.**

3. **`documentVersion = 1` is reset on every tab switch** (src/app.js:721). If a `didChange v=2` from the previous URI is still in flight, Pyright may discard a newer version. Use a per-URI version map.
   **Status: Completed - no further action needed.**

### Medium

4. **`OPFSProject.exists`** opfs-project.js:101-115 catches every error as "doesn't exist". A `QuotaExceededError` or permission failure becomes a silent false-negative. Catch `NotFoundError` specifically; rethrow others.
   **Status: Completed - no further action needed.**

5. **Synchronous `prompt()`/`confirm()`** in file-tree.js:248-273. Blocks the main thread, fails Playwright headless tests without `page.on("dialog", ...)` plumbing, and breaks accessibility. Replace with an inline rename input field. (ViperIDE has the same issue, so not a regression — but a clear next step.)
   **Status: Completed - no further action needed.**

6. **No event bus.** Every interaction is wired by callbacks threaded through constructors. Adding a status bar or search panel will require touching every component. ViperIDE dispatches `tabActivated`, `tabClosed`, `fileSaved`, `fileRenamed`, `fileRemoved`, `dirRemoved`, `editorLoaded` on `document` (app.js:1149-1164)) — components subscribe independently. Recommend adopting the same pattern.
   **Status: Completed - no further action needed.**

7. **`collectWorkspaceFiles` reads the whole project from OPFS** on every board switch / type-check mode change (src/app.js:62-83). Cheap today, but scales O(N) with files. The worker already has a copy in ZenFS — passing only delta on board switch and keeping the full snapshot worker-side would be faster.
   **Status: Completed - no further action needed.**

8. **Cascade-close on directory delete is missing.** Deleting `lib/` leaves any open `lib/foo.py` tabs orphaned. ViperIDE handles this with `dirRemoved` (editor_tabs.js:88-92).
   **Status: Completed - no further action needed.**

9. **`OPFSProject.renameFile`** is read → write → delete (not atomic). On partial failure you end up with two copies. Add a comment, and have the caller close any open tab before rename.
   **Status: Completed - no further action needed.**

10. **`LocalStorageBackend.listFiles`** linear-scans all of `localStorage` every call (opfs-project.js:131-150). Fine for small projects; cache the listing if the tree refreshes a lot.
   **Status: Completed - no further action needed.**

11. **New: duplicate `didOpen` risk on initial load after refactor.** `createViewForPath` now calls `bindLSPToView` when `lspClient` exists, and later the init path iterates `docManager.forEachView((v) => bindLSPToView(v))` again. This can emit `textDocument/didOpen` twice for already-open docs (without `didClose` in between), which violates LSP expectations and may cause subtle server-side state issues.
   **Status: Completed - no further action needed.**

12. **New: single global debounce timer across all open views.** `changeDebounceTimer` is shared by all editor instances; typing in one tab and then quickly editing another can cancel the first tab's pending `didChange`. Diagnostics may lag or skip until another edit event on that file. Use a per-URI (or per-view) debounce map instead of one global timer.
   **Status: Completed - no further action needed.**

### New Findings From Sanity Check (After Medium Fixes)

13. **High: `renameFile` rollback can delete existing destination data** (src/storage/opfs-project.js). Current rollback deletes `newPath` if `deleteFile(oldPath)` fails. If `newPath` already existed before rename, this can remove unrelated user data. Suggested fix: treat rename-over-existing as invalid, or preserve and restore pre-existing destination content during rollback.
   **Status: Completed - no further action needed.**

14. **Medium: unescaped CSS selector path interpolation in FileTree** (src/ui/file-tree.js). `querySelector(`[data-path="${path}"]`)` is used in rename/delete/new-file helpers; valid filenames containing selector-significant characters can throw/mis-select. Suggested fix: use `CSS.escape(path)` for selector construction, or avoid selector interpolation by walking known node references.
   **Status: Completed - no further action needed.**

15. **Medium: per-URI debounce timers are not cleared on close/rename/delete** (src/app.js). A pending timer can still emit `didChange` for a document after it has been closed/renamed/deleted. Suggested fix: clear and delete timer entries during close/delete/rename flows before sending lifecycle updates.
   **Status: Completed - no further action needed.**

### Low / nitpicks
Note: irrelevant review items have been removed.

12. **`onActiveChange` has no off()** — listener leak if components are recreated.
   **Status: Completed - no further action needed.**
14. **No "Untitled" placeholder tab** when the last tab closes — currently the editor goes blank with no tab. ViperIDE creates an Untitled tab automatically (editor_tabs.js:155-158).
   **Status: Completed - no further action needed.**
16. **`writePyrightConfig` redundantly lists `"."` in both `include` and `extraPaths`** — fine but a comment clarifying *why* would help future readers (`include` is what to type-check; `extraPaths` is what to import from).
   **Status: Completed - no further action needed.**
17. **pyright-worker.ts interception relies on `BrowserMessageReader` reassigning `ctx.onmessage`** (pyright-worker.ts:189-203). If a future vscode-languageserver version uses `addEventListener('message', …)` instead, this silently breaks. Add a sanity warning if `lspOnMessage` is `undefined` after init.
   **Status: Completed - no further action needed.**
18. **Tests gaps**: no coverage for rename, dir-cascade-delete, dirty-on-close, or version drift across tab switches.
   **Status: Completed - no further action needed.**

---

## Recommended ports from ViperIDE (priority order)

| # | Feature | Why | Effort |
|---|---|---|---|
| 1 | **One `EditorView` per tab pane** | Eliminates manual state/scroll/undo bookkeeping; biggest robustness win | Medium — refactor DocumentManager + app.js wiring |
| 2 | **`document.dispatchEvent` event bus** for tab/file lifecycle | Decouples components; simplifies stage 5+ features | Small |
| 3 | **Confirm-on-close-when-dirty** | User-data safety | Trivial |
| 4 | **`dirRemoved` cascade close** | Correctness when deleting folders with open tabs | Trivial |
| 5 | **Middle-click closes tab** | UX nicety | Trivial |
| 6 | **Per-extension mode dispatch** in editor factory | Future-proofing as project files diversify | Small |
| 7 | **"Untitled" placeholder when last tab closes** | Avoids empty editor without a path | Trivial |

## Verdict

Ship it as the multi-file foundation, but treat the **single-EditorView-with-state-swap** model as technical debt — moving to per-tab `EditorView` panes (ViperIDE's pattern) is the most impactful next refactor. The Pyright config and worker-message changes are correct and ready to push.