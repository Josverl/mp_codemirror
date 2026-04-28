Multi-File Project Support: Implementation Plan

Current State

The editor is a single-document playground. There is one document.py in the Pyright /workspace, one CodeMirror EditorView, and the LSP client is hardwired to file:///workspace/document.py. The worker's ZenFS /workspace already has the scaffold needed for a real workspace — we just need to populate it with more than one file.



Stage 1 — In-Browser Virtual Filesystem (OPFS)

Goal: Persist a project folder tree in the browser using the Origin Private File System API. No UI changes yet — just the storage layer.



Create src/storage/opfs-project.js — a thin wrapper around navigator.storage.getDirectory() that provides:

listFiles(path) → returns a flat list of {path, name, type} entries

readFile(path) → returns file content as string

writeFile(path, content) → writes/creates a file

deleteFile(path) → removes a file or empty directory

createDirectory(path) → creates a folder

renameFile(oldPath, newPath) → moves/renames a file



On first load, seed the project with a default main.py containing a simple MicroPython hello-world.

Persist the "last active file" key in localStorage.

Test: Write a pytest/playwright unit test that opens the page, calls the storage API from the browser console, creates a file, refreshes, and verifies it persists.



Stage 2 — File Tree UI (sidebar)

Goal: Show the project in a collapsible tree panel to the left of the editor.



Add a <div id="file-tree"> sidebar to index.html, with a resize handle, and adjust the <main> layout (flex row instead of single #editor-container).

Create src/ui/file-tree.js — renders the OPFS tree as an <ul> list:

Folder nodes are toggleable (collapsed/expanded state stored in sessionStorage).

File nodes are clickable to open them in the editor.

Context menu (right-click or icon) for: New File, New Folder, Rename, Delete.

Keyboard navigation (arrow keys, Enter to open, Delete to delete).



Active file is highlighted.

Style in styles.css: fixed width (default 220px), resizable via a drag handle, dark/light theme aware.

Test: Playwright test that opens the sidebar, creates a new file, renames it, and verifies it appears in the tree.



Stage 3 — Multi-Document CodeMirror Management

Goal: Switch between open files without losing unsaved content; each file has its own editor state.



Create src/editor/document-manager.js that holds a Map<filePath, EditorState> (in-memory cache of open files):

openFile(path) → reads from OPFS, creates or retrieves EditorState, makes it active

saveFile(path) → writes current state content back to OPFS (auto-save on switch + explicit Ctrl+S)

closeFile(path) → removes from map (after saving)

getCurrentContent(path) → returns current doc string



Wire the single existing EditorView to swap its EditorState when the user clicks a different file in the tree (using view.setState()).

Add an open-file tab bar above the editor (src/ui/tab-bar.js): one tab per open file, close button on each tab, dirty indicator (•) when unsaved changes exist.

Preserve scroll position and cursor position per-file by storing them alongside the EditorState.

Test: Open two files, edit file A, switch to file B, switch back — verify content of A is preserved.



Stage 4 — LSP Workspace Synchronization

Goal: Pyright type-checks all project files together, so cross-file imports resolve correctly.



Modify src/lsp/client.js → createLSPPlugin to accept multiple URIs. On startup, send textDocument/didOpen for every file in the project (not just document.py).

In the worker's handleInitServer (or via a new syncWorkspace message), write all project files to /workspace/ in ZenFS at init time — this lets Pyright resolve local imports immediately.

Add a new worker message type MsgSyncFile ({ type: "syncFile", path, content }) so that when the user edits or creates a file, it is written to ZenFS in real time. The worker's onmessage handler routes this message to fs.writeFileSync.

Send textDocument/didChange (or didOpen/didClose) for the currently active file as the user types (existing debounce mechanism stays).

When a new file is created or a file is deleted in the tree, send didOpen/didClose notifications and the syncFile worker message.

Test: Create two files (main.py importing from helpers.py), verify that Pyright resolves the import without error (no red squiggle on the import line).
