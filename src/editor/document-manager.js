/**
 * Document Manager
 *
 * Manages multiple open CodeMirror documents. Each open file gets its own
 * EditorState. The single EditorView swaps states when the user switches files.
 */

import { EditorState } from '@codemirror/state';
import { OPFSProject } from '../storage/opfs-project.js';

export class DocumentManager {
    /**
     * @param {import('@codemirror/view').EditorView} view
     * @param {() => import('@codemirror/state').Extension[]} getBaseExtensions
     *   Returns the base set of extensions to use for every new EditorState.
     */
    constructor(view, getBaseExtensions) {
        this._view = view;
        this._getBaseExtensions = getBaseExtensions;

        /** @type {Map<string, { state: EditorState, scrollTop: number, dirty: boolean }>} */
        this._docs = new Map();

        /** @type {string|null} */
        this._activeFile = null;

        /** @type {Array<(path: string) => void>} */
        this._changeListeners = [];
    }

    /** Register a listener called whenever the active file changes. */
    onActiveChange(fn) { this._changeListeners.push(fn); }

    _notifyListeners(path) {
        for (const fn of this._changeListeners) {
            try { fn(path); } catch (e) { console.error('DocumentManager listener error', e); }
        }
    }

    /**
     * Open a file (read from OPFS if not yet cached) and activate it.
     * @param {string} path
     */
    async openFile(path) {
        if (!this._docs.has(path)) {
            let content = '';
            try {
                content = await OPFSProject.readFile(path);
            } catch (err) {
                console.warn(`DocumentManager: could not read ${path}:`, err.message);
            }
            const shouldAdoptExistingViewState = (
                !this._activeFile
                && this._view
                && this._view.state.doc.toString() === content
            );
            const state = shouldAdoptExistingViewState
                ? this._view.state
                : EditorState.create({
                    doc: content,
                    extensions: this._getBaseExtensions(),
                });
            this._docs.set(path, { state, scrollTop: 0, dirty: false });
        }

        // Save scroll of current before switching
        if (this._activeFile && this._view) {
            const cur = this._docs.get(this._activeFile);
            if (cur) cur.scrollTop = this._view.scrollDOM.scrollTop;
        }

        this._activeFile = path;
        OPFSProject.setLastActiveFile(path);

        const entry = this._docs.get(path);
        if (this._view && this._view.state !== entry.state) {
            this._view.setState(entry.state);
            // Restore scroll after state swap (next frame)
            requestAnimationFrame(() => {
                this._view.scrollDOM.scrollTop = entry.scrollTop;
            });
        }

        this._notifyListeners(path);
    }

    /**
     * Save current in-memory state of a file back to OPFS.
     * @param {string} [path] — defaults to active file
     */
    async saveFile(path) {
        const target = path || this._activeFile;
        if (!target) return;
        const entry = this._docs.get(target);
        if (!entry) return;

        // If saving active file, sync EditorView → EditorState first
        if (target === this._activeFile && this._view) {
            entry.state = this._view.state;
        }

        const content = entry.state.doc.toString();
        await OPFSProject.writeFile(target, content);
        entry.dirty = false;
        this._notifyListeners(target);
    }

    /**
     * Close a file (auto-saves first).
     * @param {string} path
     */
    async closeFile(path) {
        await this.saveFile(path);
        this._docs.delete(path);

        if (this._activeFile === path) {
            // Activate the next open file if any
            const remaining = [...this._docs.keys()];
            if (remaining.length > 0) {
                await this.openFile(remaining[remaining.length - 1]);
            } else {
                this._activeFile = null;
                this._notifyListeners(null);
            }
        }
    }

    /**
     * Get the current text content for a path.
     * If it's the active file, reads from the live EditorView.
     * @param {string} path
     * @returns {string}
     */
    getCurrentContent(path) {
        if (path === this._activeFile && this._view) {
            return this._view.state.doc.toString();
        }
        const entry = this._docs.get(path);
        return entry ? entry.state.doc.toString() : '';
    }

    /** Mark the active file as dirty (unsaved changes). */
    markDirty() {
        if (!this._activeFile) return;
        const entry = this._docs.get(this._activeFile);
        if (entry && !entry.dirty) {
            entry.dirty = true;
            this._notifyListeners(this._activeFile);
        }
    }

    /** @returns {string|null} */
    get activeFile() { return this._activeFile; }

    /** @returns {string[]} All currently open file paths. */
    get openFiles() { return [...this._docs.keys()]; }

    /** @returns {boolean} */
    isDirty(path) {
        return this._docs.get(path)?.dirty ?? false;
    }

    /**
     * Sync the EditorState back from the view (called before switching tabs).
     */
    syncFromView() {
        if (this._activeFile && this._view) {
            const entry = this._docs.get(this._activeFile);
            if (entry) {
                entry.state = this._view.state;
            }
        }
    }
}
