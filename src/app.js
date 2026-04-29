/**
 * CodeMirror 6 MicroPython Editor
 * A simple Python code editor with syntax highlighting and basic features
 */

import { python } from '@codemirror/lang-python';
import { indentUnit } from '@codemirror/language';
import { Compartment, Prec } from '@codemirror/state';
import { EditorView, basicSetup } from 'codemirror';
import { keymap } from '@codemirror/view';
import { setDiagnostics } from '@codemirror/lint';
import { createLSPClient, createLSPPlugin, switchBoard } from './lsp/client.js';
import { restoreFromUrl, initShareDropdown } from './share.js';
import { notifyDocumentChange, notifyDocumentOpen, updateDiagnosticsStatus, lintKeymapExtension } from './lsp/diagnostics.js';
import { OPFSProject } from './storage/opfs-project.js';
import { DocumentManager } from './editor/document-manager.js';
import { TabBar } from './ui/tab-bar.js';
import { FileTree } from './ui/file-tree.js';
import { Events } from './events.js';

// Sample Python code - will be loaded from file
let sampleCode = '# Loading example...\n';

// Available example files (will be populated dynamically)
let exampleFiles = [];

// LSP client and related state
let lspClient = null;
let lspTransport = null;
let documentUri = 'file:///workspace/main.py'; // updated dynamically

// Per-URI document version tracker. Each tab maintains its own monotonically
// increasing version so that an in-flight didChange for the previously-active
// URI cannot be invalidated when the user switches tabs.
const documentVersions = new Map();
function bumpDocumentVersion(uri) {
    const next = (documentVersions.get(uri) || 0) + 1;
    documentVersions.set(uri, next);
    return next;
}
function resetDocumentVersion(uri) {
    documentVersions.set(uri, 1);
    return 1;
}
function forgetDocumentVersion(uri) {
    documentVersions.delete(uri);
}

// Board stub state
let currentBoardId = null;
let boardManifest = null;
let stubsCache = new Map(); // boardId → ArrayBuffer

// Pyright version (received from worker on init)
let pyrightVersion = "";

// Type checking mode
let currentTypeCheckMode = localStorage.getItem('mp_typeCheckMode') || 'standard';

// Per-URI debounce timers for didChange notifications
const changeDebounceTimers = new Map();

function clearPendingDidChange(path) {
    const uri = `file:///workspace/${path}`;
    const timer = changeDebounceTimers.get(uri);
    if (!timer) return;
    clearTimeout(timer);
    changeDebounceTimers.delete(uri);
}

// Multi-file state
let docManager = null;
let tabBar = null;
let fileTree = null;

// Theme + LSP compartments are now created per-view in viewMeta (see below).

const CHANGE_DEBOUNCE_MS = 300; // Wait 300ms after user stops typing
const STARTUP_REANALYZE_DELAY_MS = 50;

// Cache for collectWorkspaceFiles — invalidated on file mutations.
let _workspaceFilesCache = null;

function invalidateWorkspaceFilesCache() { _workspaceFilesCache = null; }

// TODO: The worker already holds a copy in ZenFS. A future optimisation could
// pass only deltas on board-switch / type-check-mode change instead of
// re-reading every file from OPFS each time.
async function collectWorkspaceFiles(activePath = null, activeContentOverride = null) {
    if (!_workspaceFilesCache) {
        const workspaceFiles = {};
        const allFiles = await OPFSProject.listFiles();

        for (const entry of allFiles) {
            if (entry.type !== 'file') continue;
            try {
                workspaceFiles[entry.path] = await OPFSProject.readFile(entry.path);
            } catch {
                // Ignore files that disappear during collection.
            }
        }
        _workspaceFilesCache = workspaceFiles;
    }

    // Return a shallow copy with the active document's live content overlaid.
    const result = { ..._workspaceFilesCache };
    if (activePath && activeContentOverride !== null) {
        result[activePath] = activeContentOverride;
    }
    return result;
}

async function syncWorkspaceToLSP({ openDocuments = false, activeUri = documentUri, workspaceFiles = null } = {}) {
    if (!lspClient) return;

    try {
        const files = workspaceFiles || await collectWorkspaceFiles();
        for (const [filePath, content] of Object.entries(files)) {
            const fileUri = `file:///workspace/${filePath}`;

            if (!workspaceFiles && lspTransport?.worker) {
                lspTransport.worker.postMessage({ type: 'syncFile', path: filePath, content });
            }

            if (openDocuments && fileUri !== activeUri) {
                notifyDocumentOpen(lspClient, fileUri, 'python', content, 1);
            }
        }
    } catch (err) {
        console.warn('Workspace sync failed:', err);
    }
}

function scheduleActiveDocumentRefresh(activeUri, content) {
    if (!lspClient) return;

    window.setTimeout(() => {
        if (!lspClient || documentUri !== activeUri) return;
        const v = bumpDocumentVersion(activeUri);
        notifyDocumentChange(lspClient, activeUri, content, v);
    }, STARTUP_REANALYZE_DELAY_MS);
}

// Resolve base path for assets (stubs, manifest)
function getAssetsBase() {
    return window.location.pathname.includes('/src/') ? '../assets' : './assets';
}

// Fetch board stubs manifest and populate the board selector
async function initBoardSelector() {
    const select = document.getElementById('boardSelect');
    try {
        const base = getAssetsBase();
        const resp = await fetch(`${base}/stubs-manifest.json`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        boardManifest = await resp.json();

        select.innerHTML = '';
        for (const board of boardManifest.boards) {
            const opt = document.createElement('option');
            opt.value = board.id;
            // Virtual boards (file === null) show their name; real boards show package — version
            if (board.file === null) {
                opt.textContent = board.package || board.id;
            } else {
                opt.textContent = board.package_version
                    ? `${board.package} — ${board.package_version}`
                    : board.package;
            }
            select.appendChild(opt);
        }

        // Restore saved selection or use manifest default
        const saved = localStorage.getItem('mp_board');
        currentBoardId = saved && boardManifest.boards.some(b => b.id === saved)
            ? saved
            : boardManifest.default;
        select.value = currentBoardId;

        select.addEventListener('change', handleBoardChange);
    } catch (err) {
        console.warn('Could not load board manifest:', err);
        select.innerHTML = '<option value="">Default (bundled)</option>';
    }
}

// Fetch board stub zip, using cache
async function fetchBoardStubs(boardId) {
    if (stubsCache.has(boardId)) return stubsCache.get(boardId);

    const board = boardManifest?.boards.find(b => b.id === boardId);
    if (!board) throw new Error(`Unknown board: ${boardId}`);

    // No stubs file means CPython-only — pass false to skip MicroPython stubs
    if (!board.file) {
        stubsCache.set(boardId, false);
        return false;
    }

    // Bundled board doesn't need fetching — pass undefined to use worker's default
    if (board.bundled) {
        stubsCache.set(boardId, undefined);
        return undefined;
    }

    const base = getAssetsBase();
    const resp = await fetch(`${base}/${board.file}`);
    if (!resp.ok) throw new Error(`Failed to fetch stubs for ${boardId}: HTTP ${resp.status}`);
    const data = await resp.arrayBuffer();
    stubsCache.set(boardId, data);
    return data;
}

// Handle board selector change
async function handleBoardChange(event) {
    const newBoardId = event.target.value;
    if (newBoardId === currentBoardId) return;

    const loading = document.getElementById('boardLoading');
    const select = document.getElementById('boardSelect');

    try {
        loading.hidden = false;
        select.disabled = true;

        const stubs = await fetchBoardStubs(newBoardId);
        const activePath = docManager?.activeFile || documentUri.replace('file:///workspace/', '');
        const activeContent = view ? view.state.doc.toString() : null;
        const workspaceFiles = await collectWorkspaceFiles(activePath, activeContent);

        // Determine worker URL
        const workerUrl = window.location.pathname.includes('/src/')
            ? '../dist/pyright_worker.js'
            : './pyright_worker.js';

        const result = await switchBoard(
            { client: lspClient, transport: lspTransport },
            {
                workerUrl,
                timeout: 15000,
                boardStubs: stubs,
                workspaceFiles,
                typeCheckingMode: currentTypeCheckMode,
            }
        );

        lspClient = result.client;
        lspTransport = result.transport;
        currentBoardId = newBoardId;
        localStorage.setItem('mp_board', newBoardId);

        // Clear old diagnostics and rebind LSP for every open view.
        if (docManager) {
            updateDiagnosticsStatus([], pyrightVersion);
            // Worker was restarted — every URI starts over.
            documentVersions.clear();
            const activeUri = `file:///workspace/${docManager.activeFile}`;
            await syncWorkspaceToLSP({ openDocuments: false, activeUri, workspaceFiles });
            rebindLSPAllViews();
        }

        console.log(`Switched to board: ${newBoardId}`);
    } catch (err) {
        console.error(`Board switch failed:`, err);
        // Revert UI to current board
        select.value = currentBoardId;
    } finally {
        loading.hidden = true;
        select.disabled = false;
    }
}

// Handle type checking mode change — requires worker restart
async function handleTypeCheckModeChange(event) {
    const newMode = event.target.value;
    if (newMode === currentTypeCheckMode) return;

    if (!lspClient || !lspTransport) {
        currentTypeCheckMode = newMode;
        localStorage.setItem('mp_typeCheckMode', newMode);
        return;
    }

    const loading = document.getElementById('boardLoading');
    const select = event.target;

    try {
        loading.hidden = false;
        select.disabled = true;

        const stubs = await fetchBoardStubs(currentBoardId);
        const activePath = docManager?.activeFile || documentUri.replace('file:///workspace/', '');
        const activeContent = view ? view.state.doc.toString() : null;
        const workspaceFiles = await collectWorkspaceFiles(activePath, activeContent);
        const workerUrl = window.location.pathname.includes('/src/')
            ? '../dist/pyright_worker.js'
            : './pyright_worker.js';

        const result = await switchBoard(
            { client: lspClient, transport: lspTransport },
            {
                workerUrl,
                timeout: 15000,
                boardStubs: stubs,
                workspaceFiles,
                typeCheckingMode: newMode,
            }
        );

        lspClient = result.client;
        lspTransport = result.transport;
        currentTypeCheckMode = newMode;
        localStorage.setItem('mp_typeCheckMode', newMode);

        if (docManager) {
            updateDiagnosticsStatus([], pyrightVersion);
            documentVersions.clear();
            const activeUri = `file:///workspace/${docManager.activeFile}`;
            await syncWorkspaceToLSP({ openDocuments: false, activeUri, workspaceFiles });
            rebindLSPAllViews();
        }

        console.log(`Switched to type checking mode: ${newMode}`);
    } catch (err) {
        console.error('Type check mode switch failed:', err);
        select.value = currentTypeCheckMode;
    } finally {
        loading.hidden = true;
        select.disabled = false;
    }
}

// Fetch list of example files from the examples folder
async function fetchExampleFiles() {
    try {
        // Fetch the manifest file that lists all available examples
        const manifestResponse = await fetch('./examples/examples.json');
        if (!manifestResponse.ok) {
            throw new Error('Could not load examples manifest');
        }

        const filenames = await manifestResponse.json();

        // Fetch each file to get its first comment line as description
        for (const filename of filenames) {
            try {
                const contentResponse = await fetch(`./examples/${filename}`);
                if (contentResponse.ok) {
                    const content = await contentResponse.text();
                    const firstLine = content.split('\n')[0];

                    // Extract description from first comment line
                    const description = firstLine.startsWith('#')
                        ? firstLine.substring(1).trim()
                        : filename.replace('.py', '').replace(/_/g, ' ');

                    exampleFiles.push({ name: description, file: filename });
                }
            } catch (error) {
                console.warn(`Could not load ${filename}:`, error);
            }
        }

        if (exampleFiles.length === 0) {
            console.error('No example files could be loaded');
        }
    } catch (error) {
        console.error('Error fetching example files:', error);
    }
}

// Populate the example selector dropdown
function populateExampleSelector() {
    const select = document.getElementById('sampleSelect');
    exampleFiles.forEach(example => {
        const option = document.createElement('option');
        option.value = example.file;
        option.textContent = example.name;
        select.appendChild(option);
    });

    // Set default selection to first file if available
    if (exampleFiles.length > 0) {
        select.value = exampleFiles[0].file;
    }
}

// Load sample code from file
async function loadSampleFromFile(filename = 'blink_led.py') {
    try {
        const response = await fetch(`./examples/${filename}`);
        if (response.ok) {
            sampleCode = await response.text();
        } else {
            console.error('Failed to load sample file:', response.statusText);
            sampleCode = `# Error loading ${filename}\n# Please check console for details\n`;
        }
    } catch (error) {
        console.error('Error fetching sample file:', error);
        sampleCode = `# Error loading ${filename}\n# Please check console for details\n`;
    }
}

// Theme configuration
let isDarkTheme = false;  // Default to light theme

// Dark theme
const darkTheme = EditorView.theme({
    "&": {
        backgroundColor: "#1e1e1e",
        color: "#d4d4d4",
        height: "100%"
    },
    ".cm-content": {
        caretColor: "#528bff",
        fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
        fontSize: "14px",
        lineHeight: "1.5"
    },
    ".cm-cursor, .cm-dropCursor": {
        borderLeftColor: "#528bff"
    },
    "&.cm-focused .cm-selectionBackground, ::selection": {
        backgroundColor: "#264f78"
    },
    ".cm-selectionBackground": {
        backgroundColor: "#264f7880"
    },
    "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground": {
        backgroundColor: "#4477bb"
    },
    ".cm-activeLine": {
        backgroundColor: "transparent"
    },
    ".cm-selectionMatch": {
        backgroundColor: "#3a3d41"
    },
    ".cm-gutters": {
        backgroundColor: "#1e1e1e",
        color: "#858585",
        border: "none"
    },
    ".cm-activeLineGutter": {
        backgroundColor: "#2a2a2a"
    },
    ".cm-foldPlaceholder": {
        backgroundColor: "#3a3d41",
        border: "none",
        color: "#d4d4d4"
    }
}, { dark: true });

// Light theme
const lightTheme = EditorView.theme({
    "&": {
        backgroundColor: "#ffffff",
        color: "#000000",
        height: "100%"
    },
    ".cm-content": {
        caretColor: "#0000ff",
        fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
        fontSize: "14px",
        lineHeight: "1.5"
    },
    ".cm-cursor, .cm-dropCursor": {
        borderLeftColor: "#0000ff"
    },
    "&.cm-focused .cm-selectionBackground, ::selection": {
        backgroundColor: "#add6ff"
    },
    ".cm-selectionBackground": {
        backgroundColor: "#80b4fb80"
    },
    "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground": {
        backgroundColor: "#80b4fb"
    },
    ".cm-activeLine": {
        backgroundColor: "transparent"
    },
    ".cm-selectionMatch": {
        backgroundColor: "#e8e8e8"
    },
    ".cm-gutters": {
        backgroundColor: "#f5f5f5",
        color: "#237893",
        border: "none"
    },
    ".cm-activeLineGutter": {
        backgroundColor: "#e8e8e8"
    },
    ".cm-foldPlaceholder": {
        backgroundColor: "#e8e8e8",
        border: "none",
        color: "#000000"
    }
}, { dark: false });

// Initialize the editor with basic setup and Python language support
let view;

// ---------------------------------------------------------------------------
// Editor helpers (module-level so board/type-check handlers can rebind views)
// ---------------------------------------------------------------------------

const INDENT = '    ';

function selectedLineNumbers(state) {
    const lineNumbers = new Set();
    for (const range of state.selection.ranges) {
        const startLine = state.doc.lineAt(range.from).number;
        let endLine = state.doc.lineAt(range.to).number;
        if (range.to > range.from && state.doc.lineAt(range.to).from === range.to) {
            endLine -= 1;
        }
        for (let lineNo = startLine; lineNo <= endLine; lineNo++) {
            lineNumbers.add(lineNo);
        }
    }
    return Array.from(lineNumbers).sort((a, b) => a - b);
}

function indentWithFourSpaces(targetView) {
    const { state } = targetView;
    const hasMultiline = state.selection.ranges.some((range) => (
        state.doc.lineAt(range.from).number < state.doc.lineAt(range.to).number
    ));

    if (!hasMultiline) {
        targetView.dispatch({
            ...state.replaceSelection(INDENT),
            scrollIntoView: true,
            userEvent: 'input.indent'
        });
        return true;
    }

    const changes = selectedLineNumbers(state).map((lineNo) => {
        const line = state.doc.line(lineNo);
        return { from: line.from, insert: INDENT };
    });

    targetView.dispatch({
        changes,
        scrollIntoView: true,
        userEvent: 'input.indent'
    });
    return true;
}

function dedentFourSpaces(targetView) {
    const { state } = targetView;
    const changes = [];

    for (const lineNo of selectedLineNumbers(state)) {
        const line = state.doc.line(lineNo);
        const text = line.text;
        let removeCount = 0;

        if (text.startsWith(INDENT)) {
            removeCount = 4;
        } else if (text.startsWith('\t')) {
            removeCount = 1;
        } else {
            const match = text.match(/^ {1,3}/);
            removeCount = match ? match[0].length : 0;
        }

        if (removeCount > 0) {
            changes.push({
                from: line.from,
                to: line.from + removeCount
            });
        }
    }

    if (!changes.length) {
        return true;
    }

    targetView.dispatch({
        changes,
        scrollIntoView: true,
        userEvent: 'input.indent'
    });
    return true;
}

/**
 * Per-view bookkeeping for theme/LSP compartments so we can reconfigure each
 * view independently on theme toggle / board switch.
 * @type {WeakMap<import('@codemirror/view').EditorView, {themeC: Compartment, lspC: Compartment, path: string}>}
 */
const viewMeta = new WeakMap();

function buildExtensions(path, themeC, lspC) {
    const uri = `file:///workspace/${path}`;
    const updateListener = EditorView.updateListener.of((update) => {
        if (!update.docChanged) return;
        docManager?.markDirty(path);
        if (!lspClient) return;
        const prev = changeDebounceTimers.get(uri);
        if (prev) clearTimeout(prev);
        changeDebounceTimers.set(uri, setTimeout(() => {
            changeDebounceTimers.delete(uri);
            const c = update.state.doc.toString();
            const v = bumpDocumentVersion(uri);
            console.log(`Sending didChange ${path} (version ${v})`);
            notifyDocumentChange(lspClient, uri, c, v);
            if (lspTransport?.worker) {
                lspTransport.worker.postMessage({ type: 'syncFile', path, content: c });
            }
        }, CHANGE_DEBOUNCE_MS));
    });

    return [
        basicSetup,
        indentUnit.of(INDENT),
        python(),
        Prec.high(keymap.of([
            { key: 'Tab', run: indentWithFourSpaces },
            { key: 'Shift-Tab', run: dedentFourSpaces },
            { key: 'Mod-s', run: () => { docManager?.saveFile(); return true; } },
        ])),
        themeC.of(isDarkTheme ? darkTheme : lightTheme),
        lintKeymapExtension,
        updateListener,
        lspC.of([]),
    ];
}

function createViewForPath(path, content, paneEl) {
    const themeC = new Compartment();
    const lspC = new Compartment();
    const v = new EditorView({
        doc: content,
        extensions: buildExtensions(path, themeC, lspC),
        parent: paneEl,
    });
    viewMeta.set(v, { themeC, lspC, path });
    if (lspClient) bindLSPToView(v);
    return v;
}

function bindLSPToView(v) {
    const meta = viewMeta.get(v);
    if (!meta || !lspClient) return;
    // Guard: skip if LSP is already bound (avoids duplicate didOpen)
    if (meta.lspBound) return;
    const uri = `file:///workspace/${meta.path}`;
    const content = v.state.doc.toString();
    resetDocumentVersion(uri);
    const ext = createLSPPlugin(lspClient, v, uri, 'python', content, pyrightVersion);
    v.dispatch({ effects: meta.lspC.reconfigure(ext) });
    meta.lspBound = true;
}

function clearLSPOnView(v) {
    const meta = viewMeta.get(v);
    if (!meta) return;
    v.dispatch(setDiagnostics(v.state, []));
    v.dispatch({ effects: meta.lspC.reconfigure([]) });
    meta.lspBound = false;
}

function reconfigureThemeOnAllViews() {
    const themeExt = isDarkTheme ? darkTheme : lightTheme;
    docManager?.forEachView((v) => {
        const meta = viewMeta.get(v);
        if (meta) v.dispatch({ effects: meta.themeC.reconfigure(themeExt) });
    });
}

function rebindLSPAllViews() {
    docManager?.forEachView((v) => {
        clearLSPOnView(v);
        bindLSPToView(v);
    });
    updateDiagnosticsStatus([], pyrightVersion);
}

// Initialize editor after loading sample
async function initializeEditor() {
    // Check URL parameters first (shareable link)
    const urlState = await restoreFromUrl();

    // If URL specifies a board, apply it before board selector init
    if (urlState.board) {
        localStorage.setItem('mp_board', urlState.board);
    }

    // If URL specifies typeCheckMode, apply it
    if (urlState.typeCheckMode) {
        currentTypeCheckMode = urlState.typeCheckMode;
        localStorage.setItem('mp_typeCheckMode', urlState.typeCheckMode);
        document.getElementById('typeCheckMode').value = urlState.typeCheckMode;
    }

    // Fetch available examples and board manifest in parallel
    await Promise.all([
        fetchExampleFiles(),
        initBoardSelector(),
    ]);

    // Use code from URL if present, otherwise load first example
    if (urlState.code) {
        sampleCode = urlState.code;
    } else {
        const defaultFile = exampleFiles.length > 0 ? exampleFiles[0].file : 'blink_led.py';
        await loadSampleFromFile(defaultFile);
    }

    // Initialize OPFS storage before starting LSP so the worker can preload the project.
    await OPFSProject.init();

    // If loaded from a shareable URL, put the code in main.py.
    if (urlState.code) {
        await OPFSProject.writeFile('main.py', urlState.code);
    }

    // Determine the initial file and content before the worker starts.
    const initialFile = OPFSProject.getLastActiveFile();
    documentUri = `file:///workspace/${initialFile}`;

    let initialContent;
    try {
        initialContent = await OPFSProject.readFile(initialFile);
    } catch {
        initialContent = sampleCode;
    }

    const initialWorkspaceFiles = await collectWorkspaceFiles(initialFile, initialContent);

    // Initialize LSP client — Pyright runs in a Web Worker
    try {
        // In dev, pyright_worker.js lives at /dist/pyright_worker.js;
        // in production (deploy) it's alongside index.html.
        const workerUrl = window.location.pathname.includes('/src/')
            ? '../dist/pyright_worker.js'
            : './pyright_worker.js';
        let initialBoardStubs;
        if (currentBoardId && boardManifest) {
            try {
                initialBoardStubs = await fetchBoardStubs(currentBoardId);
            } catch (error) {
                console.warn('Could not preload stubs for board:', currentBoardId, error);
            }
        }

        window.__lspReady = false;
        window.__lspFailed = false;
        console.log('Initializing LSP client...');
        const lspResult = await createLSPClient({
            workerUrl,
            timeout: 15000,
            boardStubs: initialBoardStubs,
            workspaceFiles: initialWorkspaceFiles,
            typeCheckingMode: currentTypeCheckMode,
        });
        lspClient = lspResult.client;
        lspTransport = lspResult.transport;
        pyrightVersion = lspResult.pyrightVersion || "";
        console.log('LSP client ready.');
        window.__lspReady = true;
    } catch (error) {
        console.error('Failed to initialize LSP client:', error);
        console.log('Editor will continue without LSP features');
        window.__lspFailed = true;
    }

    // Per-view update listeners are wired inside buildExtensions(); no
    // module-level update listener is needed.

    // Create document manager rooted at the editor container
    const editorContainerEl = document.getElementById('editor-container');
    docManager = new DocumentManager(editorContainerEl, createViewForPath);
    docManager.onActiveChange((path) => {
        // Keep the module-level `view` and `documentUri` in sync with whichever
        // pane is active so existing callsites (share, export, triggerTypeCheck,
        // etc.) keep working unchanged.
        view = docManager.activeView;
        if (path) documentUri = `file:///workspace/${path}`;
    });

    await docManager.openFile(initialFile);

    // Create tab bar
    const tabBarEl = document.getElementById('tab-bar');
    tabBar = new TabBar(tabBarEl, {
        onSelect: async (path) => {
            if (path === docManager.activeFile) return;
            await docManager.openFile(path);
            refreshTabBar();
        },
        onClose: async (path) => {
            if (docManager.isDirty(path)) {
                const filename = path.split('/').pop();
                if (!confirm(`${filename} has unsaved changes. Close without saving?`)) {
                    return;
                }
                // User chose to discard — drop the dirty flag so closeFile
                // doesn't auto-save the unwanted edits back to OPFS.
                docManager.discard(path);
            }
            clearPendingDidChange(path);
            await docManager.closeFile(path);
            forgetDocumentVersion(`file:///workspace/${path}`);
            refreshTabBar();
        },
    });

    // Create file tree
    const fileTreeEl = document.getElementById('file-tree');
    fileTree = new FileTree(fileTreeEl, {
        onOpen: async (path) => {
            if (path === docManager.activeFile) return;
            await docManager.openFile(path);
            refreshTabBar();
            fileTree.setActiveFile(path);
        },
        onDelete: async (path) => {
            // Cascade-close: if a directory is deleted, close all open files
            // whose paths fall under it (e.g. deleting "lib/" closes "lib/foo.py").
            const prefix = path.endsWith('/') ? path : path + '/';
            for (const openPath of docManager.openFiles) {
                if (openPath === path || openPath.startsWith(prefix)) {
                    clearPendingDidChange(openPath);
                    docManager.discard(openPath);
                    await docManager.closeFile(openPath);
                    forgetDocumentVersion(`file:///workspace/${openPath}`);
                }
            }
            refreshTabBar();
        },
        onRename: async (oldPath, newPath) => {
            if (docManager.openFiles.includes(oldPath)) {
                clearPendingDidChange(oldPath);
                clearPendingDidChange(newPath);
                const content = docManager.getCurrentContent(oldPath);
                docManager.discard(oldPath);
                await docManager.closeFile(oldPath);
                forgetDocumentVersion(`file:///workspace/${oldPath}`);
                await OPFSProject.writeFile(newPath, content);
                await docManager.openFile(newPath);
            }
            refreshTabBar();
        },
        onRefresh: () => refreshTabBar(),
        onClearAll: async () => {
            for (const openPath of [...docManager.openFiles]) {
                clearPendingDidChange(openPath);
                docManager.discard(openPath);
                await docManager.closeFile(openPath);
                forgetDocumentVersion(`file:///workspace/${openPath}`);
            }
            refreshTabBar();
        },
    });
    await fileTree.refresh();
    fileTree.setActiveFile(initialFile);

    // Wire sidebar resize handle
    initSidebarResize();

    // Invalidate workspace-files cache on any file mutation
    for (const evt of [Events.FILE_CREATED, Events.FILE_RENAMED, Events.FILE_DELETED, Events.FILE_SAVED]) {
        document.addEventListener(evt, invalidateWorkspaceFilesCache);
    }

    // Helper: update tab bar display
    function refreshTabBar() {
        tabBar.update({
            openFiles: docManager.openFiles,
            activeFile: docManager.activeFile,
            isDirty: (p) => docManager.isDirty(p),
        });
        if (docManager.activeFile) fileTree.setActiveFile(docManager.activeFile);
    }
    refreshTabBar();

    // Bind LSP to any views that were opened before the LSP client was ready.
    if (lspClient) {
        try {
            await syncWorkspaceToLSP({
                openDocuments: false,
                activeUri: documentUri,
                workspaceFiles: initialWorkspaceFiles,
            });
            docManager.forEachView((v) => bindLSPToView(v));
            console.log('LSP plugin bound to all open views');
            scheduleActiveDocumentRefresh(documentUri, initialContent);
        } catch (error) {
            console.error('Failed to bind LSP plugin:', error);
        }
    }

    // Populate the example selector after editor is initialized
    populateExampleSelector();

    // Initialize share dropdown
    initShareDropdown(
        () => view.state.doc.toString(),
        () => currentBoardId,
        () => currentTypeCheckMode,
    );

    // Wire Export / Import buttons
    initExportImport();

    // If loaded from a shareable link, clear URL params
    if (urlState.code) {
        const cleanUrl = window.location.pathname + window.location.hash;
        window.history.replaceState(null, '', cleanUrl);
    }

    console.log('CodeMirror Python Editor initialized successfully!');
}

// Start initialization
initializeEditor();

// Sidebar resize handle
function initSidebarResize() {
    const handle = document.getElementById('sidebar-resize-handle');
    const panel = document.getElementById('file-tree-panel');
    if (!handle || !panel) return;

    let dragging = false;
    let startX = 0;
    let startWidth = 0;

    handle.addEventListener('mousedown', (e) => {
        dragging = true;
        startX = e.clientX;
        startWidth = panel.offsetWidth;
        handle.classList.add('dragging');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', (e) => {
        if (!dragging) return;
        const delta = e.clientX - startX;
        const newWidth = Math.max(100, Math.min(600, startWidth + delta));
        panel.style.width = `${newWidth}px`;
    });

    document.addEventListener('mouseup', () => {
        if (!dragging) return;
        dragging = false;
        handle.classList.remove('dragging');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
    });
}

// Export/Import wiring
function initExportImport() {
    const exportBtn = document.getElementById('exportBtn');
    const importFile = document.getElementById('importFile');

    if (exportBtn) {
        exportBtn.addEventListener('click', exportProjectAsZip);
    }

    if (importFile) {
        importFile.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            if (file.name.endsWith('.zip')) {
                await importZip(file);
            } else if (file.name.endsWith('.py')) {
                await importPyFile(file);
            }
            e.target.value = '';
        });
    }
}

async function exportProjectAsZip() {
    // Use fflate loaded from CDN for zero-dependency zip
    const { strToU8, zipSync } = await import('https://esm.sh/fflate@0.8.2');
    const files = await OPFSProject.listFiles();
    const zipFiles = {};
    for (const entry of files) {
        if (entry.type === 'file') {
            const content = await OPFSProject.readFile(entry.path);
            zipFiles[entry.path] = strToU8(content);
        }
    }
    const zipped = zipSync(zipFiles);
    const blob = new Blob([zipped], { type: 'application/zip' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'mp_project.zip';
    a.click();
    URL.revokeObjectURL(a.href);
}

async function importZip(file) {
    const { unzipSync, strFromU8 } = await import('https://esm.sh/fflate@0.8.2');
    const buf = await file.arrayBuffer();
    const unzipped = unzipSync(new Uint8Array(buf));
    for (const [path, data] of Object.entries(unzipped)) {
        if (path.endsWith('/')) continue; // directory entry
        const content = strFromU8(data);
        await OPFSProject.writeFile(path, content);
    }
    if (fileTree) await fileTree.refresh();
    console.log('Imported ZIP:', file.name);
}

async function importPyFile(file) {
    const content = await file.text();
    await OPFSProject.writeFile(file.name, content);
    if (fileTree) await fileTree.refresh();
    if (docManager) await docManager.openFile(file.name);
}


function toggleTheme() {
    isDarkTheme = !isDarkTheme;
    document.body.classList.toggle('light-theme', !isDarkTheme);
    document.body.classList.toggle('dark-theme', isDarkTheme);

    // Reconfigure the editor theme on every open view
    reconfigureThemeOnAllViews();
}

// Trigger type checking with Pyright
function triggerTypeCheck() {
    if (!lspClient || !lspClient.connected) {
        console.warn('LSP client not connected. Cannot run type check.');
        alert('LSP client not connected. Make sure the Pyright server is running.');
        return;
    }

    try {
        const content = view.state.doc.toString();
        const v = bumpDocumentVersion(documentUri);

        console.log('Triggering type check...');
        notifyDocumentChange(lspClient, documentUri, content, v);
        console.log('Type check notification sent');

        // Visual feedback
        const button = document.getElementById('typeCheckBtn');
        const originalText = button.textContent;
        button.textContent = '⏳ Checking...';
        button.disabled = true;

        // Re-enable button after a short delay
        setTimeout(() => {
            button.textContent = originalText;
            button.disabled = false;
        }, 200);
    } catch (error) {
        console.error('Error triggering type check:', error);
        alert('Failed to run type check. Check console for details.');
    }
}

// Load sample code from selected file
async function loadSample() {
    const select = document.getElementById('sampleSelect');
    const filename = select.value;

    if (!filename) {
        alert('Please select an example file first');
        return;
    }

    await loadSampleFromFile(filename);
    const transaction = view.state.update({
        changes: { from: 0, to: view.state.doc.length, insert: sampleCode }
    });
    view.dispatch(transaction);
    view.focus();

    // Automatically trigger type check after loading a new example
    setTimeout(() => {
        triggerTypeCheck();
    }, 300); // Small delay to ensure editor update is complete
}

// Get editor content (useful for future integrations)
export function getEditorContent() {
    return view.state.doc.toString();
}

// Set editor content (useful for future integrations)
export function setEditorContent(content) {
    const transaction = view.state.update({
        changes: { from: 0, to: view.state.doc.length, insert: content }
    });
    view.dispatch(transaction);
}

// Event listeners
document.getElementById('themeToggle').addEventListener('click', toggleTheme);
document.getElementById('typeCheckBtn').addEventListener('click', triggerTypeCheck);
document.getElementById('helpBtn').addEventListener('click', () => {
    const panel = document.getElementById('keyboard-help');
    panel.hidden = !panel.hidden;
});
document.getElementById('loadSampleBtn').addEventListener('click', loadSample);
document.getElementById('typeCheckMode').addEventListener('change', handleTypeCheckModeChange);

// Restore saved type checking mode
const savedTypeCheckMode = localStorage.getItem('mp_typeCheckMode');
if (savedTypeCheckMode) {
    document.getElementById('typeCheckMode').value = savedTypeCheckMode;
    currentTypeCheckMode = savedTypeCheckMode;
}

// Initialize with light theme
document.body.classList.add('light-theme');

// Export the view for testing purposes
export { view };
