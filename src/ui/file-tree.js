/**
 * File Tree UI
 *
 * Renders the OPFS project as a collapsible sidebar tree.
 * Features:
 *  - Folder nodes toggleable (state in sessionStorage)
 *  - File nodes open on click
 *  - Context-menu (or icon buttons) for New File, New Folder, Rename, Delete
 *  - Keyboard navigation: arrows, Enter to open, Delete to delete
 *  - Active file highlighted
 */

import { OPFSProject } from '../storage/opfs-project.js';
import { Events, dispatch } from '../events.js';

const EXPANDED_KEY = 'mp_tree_expanded';

function loadExpanded() {
    try { return new Set(JSON.parse(sessionStorage.getItem(EXPANDED_KEY) || '[]')); }
    catch { return new Set(); }
}
function saveExpanded(set) {
    sessionStorage.setItem(EXPANDED_KEY, JSON.stringify([...set]));
}

export class FileTree {
    /**
     * @param {HTMLElement} container
     * @param {object} callbacks
     * @param {(path: string) => void} callbacks.onOpen
     * @param {(path: string) => Promise<void>} [callbacks.onDelete]
     * @param {(path: string) => Promise<void>} [callbacks.onRename]
     * @param {() => void} [callbacks.onRefresh]
     */
    constructor(container, { onOpen, onDelete, onRename, onRefresh }) {
        this._container = container;
        this._onOpen = onOpen;
        this._onDelete = onDelete;
        this._onRename = onRename;
        this._onRefresh = onRefresh;
        this._expanded = loadExpanded();
        this._activeFile = null;
        this._entries = [];
        container.classList.add('file-tree');

        // Header with "New file" button
        this._header = document.createElement('div');
        this._header.className = 'file-tree__header';

        const title = document.createElement('span');
        title.className = 'file-tree__title';
        title.textContent = 'Files';

        const newFileBtn = document.createElement('button');
        newFileBtn.className = 'file-tree__icon-btn';
        newFileBtn.title = 'New file';
        newFileBtn.textContent = '+';
        newFileBtn.addEventListener('click', () => this._promptNewFile(''));

        this._header.appendChild(title);
        this._header.appendChild(newFileBtn);
        container.appendChild(this._header);

        this._list = document.createElement('ul');
        this._list.className = 'file-tree__list';
        this._list.setAttribute('role', 'tree');
        container.appendChild(this._list);
    }

    setActiveFile(path) {
        this._activeFile = path;
        this._render();
    }

    async refresh() {
        this._entries = await OPFSProject.listFiles();
        this._render();
    }

    // ---- Rendering ----

    _render() {
        this._list.innerHTML = '';
        // Build a tree structure from flat entries
        const tree = this._buildTree(this._entries);
        this._renderTree(tree, this._list, '');
    }

    _buildTree(entries) {
        const root = { children: {} };
        for (const entry of entries) {
            const parts = entry.path.split('/');
            let node = root;
            for (let i = 0; i < parts.length; i++) {
                const part = parts[i];
                if (!node.children[part]) {
                    node.children[part] = {
                        name: part,
                        path: parts.slice(0, i + 1).join('/'),
                        type: i === parts.length - 1 ? entry.type : 'directory',
                        children: {},
                    };
                }
                node = node.children[part];
            }
        }
        return root;
    }

    _renderTree(node, ulEl, _prefix) {
        const sorted = Object.values(node.children).sort((a, b) => {
            // Directories first, then alphabetical
            if (a.type !== b.type) return a.type === 'directory' ? -1 : 1;
            return a.name.localeCompare(b.name);
        });

        for (const child of sorted) {
            const li = document.createElement('li');
            li.setAttribute('role', 'treeitem');
            li.dataset.path = child.path;

            if (child.type === 'directory') {
                this._renderDirNode(child, li);
            } else {
                this._renderFileNode(child, li);
            }

            ulEl.appendChild(li);
        }
    }

    _renderDirNode(child, li) {
        const isExpanded = this._expanded.has(child.path);
        li.classList.add('file-tree__dir');
        li.setAttribute('aria-expanded', String(isExpanded));

        const row = document.createElement('div');
        row.className = 'file-tree__row';
        row.tabIndex = 0;

        const arrow = document.createElement('span');
        arrow.className = 'file-tree__arrow';
        arrow.textContent = isExpanded ? '▾' : '▸';

        const label = document.createElement('span');
        label.className = 'file-tree__name';
        label.textContent = child.name;

        const actions = this._makeActions(child.path, true);

        row.appendChild(arrow);
        row.appendChild(label);
        row.appendChild(actions);
        li.appendChild(row);

        row.addEventListener('click', () => this._toggleDir(child.path, li, arrow));
        row.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') this._toggleDir(child.path, li, arrow);
        });

        if (isExpanded && Object.keys(child.children).length > 0) {
            const subUl = document.createElement('ul');
            subUl.setAttribute('role', 'group');
            this._renderTree(child, subUl, child.path);
            li.appendChild(subUl);
        }
    }

    _renderFileNode(child, li) {
        li.classList.add('file-tree__file');
        if (child.path === this._activeFile) li.classList.add('file-tree__file--active');

        const row = document.createElement('div');
        row.className = 'file-tree__row';
        row.tabIndex = 0;

        const icon = document.createElement('span');
        icon.className = 'file-tree__icon';
        icon.textContent = '  ';

        const label = document.createElement('span');
        label.className = 'file-tree__name';
        label.textContent = child.name;

        const actions = this._makeActions(child.path, false);

        row.appendChild(icon);
        row.appendChild(label);
        row.appendChild(actions);
        li.appendChild(row);

        row.addEventListener('click', () => this._onOpen(child.path));
        row.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this._onOpen(child.path);
            if (e.key === 'Delete') this._deleteEntry(child.path);
        });
    }

    _makeActions(path, isDir) {
        const wrap = document.createElement('span');
        wrap.className = 'file-tree__actions';

        if (isDir) {
            const newFileBtn = document.createElement('button');
            newFileBtn.className = 'file-tree__icon-btn';
            newFileBtn.title = 'New file here';
            newFileBtn.textContent = '+';
            newFileBtn.addEventListener('click', (e) => { e.stopPropagation(); this._promptNewFile(path); });
            wrap.appendChild(newFileBtn);
        }

        const renameBtn = document.createElement('button');
        renameBtn.className = 'file-tree__icon-btn';
        renameBtn.title = 'Rename';
        renameBtn.textContent = '✎';
        renameBtn.addEventListener('click', (e) => { e.stopPropagation(); this._promptRename(path); });

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'file-tree__icon-btn file-tree__icon-btn--danger';
        deleteBtn.title = 'Delete';
        deleteBtn.textContent = '✕';
        deleteBtn.addEventListener('click', (e) => { e.stopPropagation(); this._deleteEntry(path); });

        wrap.appendChild(renameBtn);
        wrap.appendChild(deleteBtn);
        return wrap;
    }

    _toggleDir(path, li, arrow) {
        const expanded = this._expanded.has(path);
        if (expanded) {
            this._expanded.delete(path);
            arrow.textContent = '▸';
            li.setAttribute('aria-expanded', 'false');
            const sub = li.querySelector('ul');
            if (sub) sub.remove();
        } else {
            this._expanded.add(path);
            arrow.textContent = '▾';
            li.setAttribute('aria-expanded', 'true');
        }
        saveExpanded(this._expanded);
        this._render();
    }

    // ---- Mutations ----

    /**
     * Show an inline text input in the tree for new-file or rename operations.
     * Resolves with the entered value or null if cancelled (Escape / blur).
     */
    _showInlineInput(parentEl, defaultValue = '') {
        return new Promise((resolve) => {
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'file-tree__inline-input';
            input.value = defaultValue;
            parentEl.appendChild(input);
            input.focus();
            input.select();

            let settled = false;
            const finish = (value) => {
                if (settled) return;
                settled = true;
                input.remove();
                resolve(value);
            };

            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') { e.preventDefault(); finish(input.value.trim()); }
                if (e.key === 'Escape') { e.preventDefault(); finish(null); }
                e.stopPropagation();
            });
            input.addEventListener('blur', () => finish(null));
        });
    }

    /**
     * Show an inline confirm element for destructive actions.
     * Resolves true (confirmed) or false (cancelled).
     */
    _showInlineConfirm(parentEl, message) {
        return new Promise((resolve) => {
            const wrap = document.createElement('span');
            wrap.className = 'file-tree__inline-confirm';

            const label = document.createElement('span');
            label.textContent = message;

            const yesBtn = document.createElement('button');
            yesBtn.className = 'file-tree__icon-btn file-tree__icon-btn--danger';
            yesBtn.textContent = '✓';
            yesBtn.title = 'Confirm delete';

            const noBtn = document.createElement('button');
            noBtn.className = 'file-tree__icon-btn';
            noBtn.textContent = '✕';
            noBtn.title = 'Cancel';

            wrap.appendChild(label);
            wrap.appendChild(yesBtn);
            wrap.appendChild(noBtn);
            parentEl.appendChild(wrap);

            let settled = false;
            const finish = (val) => { if (!settled) { settled = true; wrap.remove(); resolve(val); } };
            yesBtn.addEventListener('click', (e) => { e.stopPropagation(); finish(true); });
            noBtn.addEventListener('click', (e) => { e.stopPropagation(); finish(false); });
        });
    }

    _findPathNode(path) {
        const nodes = this._list.querySelectorAll('[data-path]');
        for (const node of nodes) {
            if (node.dataset.path === path) return node;
        }
        return null;
    }

    async _promptNewFile(dirPath) {
        const li = this._findPathNode(dirPath) || this._list;
        const name = await this._showInlineInput(li, '');
        if (!name) return;
        const fullPath = dirPath ? `${dirPath}/${name}` : name;
        await OPFSProject.writeFile(fullPath, '');
        dispatch(Events.FILE_CREATED, { path: fullPath });
        await this.refresh();
        this._onOpen(fullPath);
        if (this._onRefresh) this._onRefresh();
    }

    async _promptRename(path) {
        const li = this._findPathNode(path);
        if (!li) return;
        const parts = path.split('/');
        const oldName = parts[parts.length - 1];
        const newName = await this._showInlineInput(li, oldName);
        if (!newName || newName === oldName) return;
        const newPath = [...parts.slice(0, -1), newName].join('/');
        await OPFSProject.renameFile(path, newPath);
        dispatch(Events.FILE_RENAMED, { oldPath: path, newPath });
        if (this._onRename) await this._onRename(path, newPath);
        await this.refresh();
        if (this._onRefresh) this._onRefresh();
    }

    async _deleteEntry(path) {
        const li = this._findPathNode(path);
        if (!li) return;
        const confirmed = await this._showInlineConfirm(li, `Delete?`);
        if (!confirmed) return;
        await OPFSProject.deleteFile(path);
        dispatch(Events.FILE_DELETED, { path });
        if (this._onDelete) await this._onDelete(path);
        await this.refresh();
        if (this._onRefresh) this._onRefresh();
    }
}
