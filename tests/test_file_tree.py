"""
Tests for File Tree UI (Stage 2)

Verifies that the file tree sidebar renders, that files can be created
and appear in the tree, and that clicking a file opens it in the editor.
"""

import pytest
import time

pytestmark = pytest.mark.editor

CDN_TIMEOUT = 15_000


def _load_editor(page, live_server):
    page.goto(f"{live_server}/index.html", wait_until="domcontentloaded")
    page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)
    time.sleep(1)


class TestFileTreeUI:
    def test_file_tree_panel_visible(self, page, live_server):
        """#file-tree-panel is rendered and visible."""
        _load_editor(page, live_server)
        panel = page.locator("#file-tree-panel")
        assert panel.count() > 0, "#file-tree-panel should exist in DOM"

    def test_file_tree_shows_main_py(self, page, live_server):
        """main.py appears in the file tree after init."""
        _load_editor(page, live_server)
        # Wait for tree to render
        page.wait_for_function(
            "() => document.querySelector('.file-tree__list') !== null",
            timeout=5000,
        )
        time.sleep(0.5)
        tree_text = page.locator(".file-tree__list").inner_text()
        assert "main.py" in tree_text, f"main.py not found in file tree: {tree_text!r}"

    def test_tab_bar_rendered(self, page, live_server):
        """#tab-bar is rendered."""
        _load_editor(page, live_server)
        assert page.locator("#tab-bar").count() > 0, "#tab-bar should exist"

    def test_tab_bar_shows_active_file(self, page, live_server):
        """Tab bar shows at least one tab after editor init."""
        _load_editor(page, live_server)
        page.wait_for_function(
            "() => document.querySelector('.tab-bar__tab') !== null",
            timeout=8000,
        )
        tabs = page.locator(".tab-bar__tab")
        assert tabs.count() >= 1, "At least one tab should be open"

    def test_sidebar_resize_handle_exists(self, page, live_server):
        """Resize handle between sidebar and editor is present."""
        _load_editor(page, live_server)
        handle = page.locator("#sidebar-resize-handle")
        assert handle.count() > 0, "#sidebar-resize-handle should be in DOM"

    def test_new_file_via_tree_header_button(self, page, live_server):
        """Clicking the + button in the tree header opens inline input; Enter creates the file."""
        _load_editor(page, live_server)
        page.wait_for_function(
            "() => document.querySelector('.file-tree__header') !== null",
            timeout=5000,
        )

        page.locator(".file-tree__header .file-tree__icon-btn").first.click()
        page.wait_for_selector(".file-tree__inline-input", timeout=3000)
        page.locator(".file-tree__inline-input").fill("tree_created.py")
        page.keyboard.press("Enter")
        time.sleep(0.5)

        # The file should now appear in the tree
        tree_text = page.locator(".file-tree__list").inner_text()
        assert "tree_created.py" in tree_text, \
            f"tree_created.py should appear in tree after creation: {tree_text!r}"

    def test_rename_handles_selector_special_chars(self, page, live_server):
        """Rename flow works for file paths containing selector-significant characters."""
        _load_editor(page, live_server)

        result = page.evaluate("""
            async () => {
                const mod = await import('./storage/opfs-project.js');
                await mod.OPFSProject.writeFile('a"b].py', '# special');
                location.reload();
                return true;
            }
        """)
        assert result is True

        page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)
        page.wait_for_selector(".file-tree__list", timeout=5000)
        time.sleep(0.6)

        rename_result = page.evaluate("""
            () => {
                const items = [...document.querySelectorAll('.file-tree__file')];
                const row = items.find((node) => node.dataset.path === 'a"b].py');
                if (!row) return { ok: false, reason: 'row-not-found' };
                const btn = row.querySelector('button[title="Rename"]');
                if (!btn) return { ok: false, reason: 'rename-button-not-found' };
                btn.click();
                const input = document.querySelector('.file-tree__inline-input');
                return { ok: !!input };
            }
        """)
        assert rename_result["ok"], f"rename input should open for special-char path: {rename_result}"

    def test_export_button_exists(self, page, live_server):
        """Export button is present in the header."""
        _load_editor(page, live_server)
        btn = page.locator("#exportBtn")
        assert btn.count() > 0, "#exportBtn should exist"

    def test_import_input_exists(self, page, live_server):
        """Import file input is present."""
        _load_editor(page, live_server)
        inp = page.locator("#importFile")
        assert inp.count() > 0, "#importFile should exist"
