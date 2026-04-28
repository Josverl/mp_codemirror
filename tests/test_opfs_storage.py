"""
Tests for OPFS Project Storage (Stage 1)

Verifies the browser-side OPFS storage API via Playwright console evaluation.
These tests use the page's JS context to exercise OPFSProject directly.
"""

import pytest
import time

pytestmark = pytest.mark.editor

CDN_TIMEOUT = 15_000


def _load_editor(page, live_server):
    page.goto(f"{live_server}/index.html")
    page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)
    # Wait until OPFSProject is ready (init called in app.js)
    page.wait_for_function(
        "() => typeof window !== 'undefined'",
        timeout=5000,
    )
    time.sleep(1)  # let async init settle


def _import_opfs(page):
    """Import OPFSProject into page context for testing."""
    return page.evaluate("""
        async () => {
            if (!window._opfsReady) {
                const mod = await import('./storage/opfs-project.js');
                window.OPFSProject = mod.OPFSProject;
                window._opfsReady = true;
            }
            return true;
        }
    """)


class TestOPFSStorage:
    def test_opfs_init_seeds_main_py(self, page, live_server):
        """After init, main.py should exist in OPFS."""
        _load_editor(page, live_server)
        _import_opfs(page)

        exists = page.evaluate("""
            async () => {
                await window.OPFSProject.init();
                return window.OPFSProject.exists('main.py');
            }
        """)
        assert exists, "main.py should be seeded on first init"

    def test_write_and_read_file(self, page, live_server):
        """writeFile then readFile returns the same content."""
        _load_editor(page, live_server)
        _import_opfs(page)

        content = page.evaluate("""
            async () => {
                await window.OPFSProject.writeFile('test_rw.py', '# hello');
                return window.OPFSProject.readFile('test_rw.py');
            }
        """)
        assert content == "# hello", f"Unexpected content: {content!r}"

    def test_list_files_includes_written_file(self, page, live_server):
        """listFiles returns an entry for a file we wrote."""
        _load_editor(page, live_server)
        _import_opfs(page)

        entries = page.evaluate("""
            async () => {
                await window.OPFSProject.writeFile('list_test.py', '');
                const files = await window.OPFSProject.listFiles();
                return files.map(e => e.path);
            }
        """)
        assert any('list_test.py' in p for p in entries), f"list_test.py not in {entries}"

    def test_delete_file(self, page, live_server):
        """deleteFile removes the file."""
        _load_editor(page, live_server)
        _import_opfs(page)

        exists_after = page.evaluate("""
            async () => {
                await window.OPFSProject.writeFile('to_delete.py', '# temp');
                await window.OPFSProject.deleteFile('to_delete.py');
                return window.OPFSProject.exists('to_delete.py');
            }
        """)
        assert not exists_after, "File should be gone after deleteFile"

    def test_rename_file(self, page, live_server):
        """renameFile moves content and removes old path."""
        _load_editor(page, live_server)
        _import_opfs(page)

        result = page.evaluate("""
            async () => {
                await window.OPFSProject.writeFile('old_name.py', '# renamed');
                await window.OPFSProject.renameFile('old_name.py', 'new_name.py');
                const newExists = await window.OPFSProject.exists('new_name.py');
                const oldExists = await window.OPFSProject.exists('old_name.py');
                const content = await window.OPFSProject.readFile('new_name.py');
                return { newExists, oldExists, content };
            }
        """)
        assert result['newExists'], "new_name.py should exist"
        assert not result['oldExists'], "old_name.py should be gone"
        assert result['content'] == '# renamed'

    def test_last_active_file_persists(self, page, live_server):
        """setLastActiveFile persists across calls within same session."""
        _load_editor(page, live_server)
        _import_opfs(page)

        result = page.evaluate("""
            () => {
                window.OPFSProject.setLastActiveFile('helpers.py');
                return window.OPFSProject.getLastActiveFile();
            }
        """)
        assert result == 'helpers.py'

    def test_file_persists_after_reload(self, page, live_server):
        """A file written in one page load is readable after reload."""
        _load_editor(page, live_server)
        _import_opfs(page)

        page.evaluate("""
            async () => {
                await window.OPFSProject.init();
                await window.OPFSProject.writeFile('persist_test.py', '# persisted');
            }
        """)

        # Reload the page
        page.reload()
        page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)
        time.sleep(1)
        _import_opfs(page)

        content = page.evaluate("""
            async () => {
                return window.OPFSProject.readFile('persist_test.py');
            }
        """)
        assert content == '# persisted', f"Expected persisted content, got {content!r}"
