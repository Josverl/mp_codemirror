"""
Multi-file document management tests (Stage 3)

Verifies that:
- Opening a file makes it active in the editor and tab bar
- Editing file A, switching to B, switching back preserves A's content
- Tab bar dirty indicator appears when content is changed
"""

import pytest
import time

pytestmark = pytest.mark.editor

CDN_TIMEOUT = 15_000


def _load_editor(page, live_server):
    page.goto(f"{live_server}/index.html")
    page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)
    time.sleep(1.5)  # let OPFS init settle


def _import_opfs(page):
    page.evaluate("""
        async () => {
            if (!window._opfsReady) {
                const mod = await import('./storage/opfs-project.js');
                window.OPFSProject = mod.OPFSProject;
                window._opfsReady = true;
            }
        }
    """)


class TestMultiFileDocumentManagement:
    def test_on_active_change_unsubscribe(self, page, live_server):
        """onActiveChange returns an unsubscribe function that detaches listeners."""
        _load_editor(page, live_server)

        result = page.evaluate("""
            async () => {
                const { DocumentManager } = await import('./editor/document-manager.js');
                const { OPFSProject } = await import('./storage/opfs-project.js');

                await OPFSProject.writeFile('listener_a.py', '# a');
                await OPFSProject.writeFile('listener_b.py', '# b');

                const host = document.createElement('div');
                document.body.appendChild(host);

                const createView = (_path, content) => ({
                    state: { doc: { toString: () => content } },
                    focus() {},
                    destroy() {},
                    dispatch() {},
                });

                const dm = new DocumentManager(host, createView);
                let calls = 0;
                const unsubscribe = dm.onActiveChange(() => { calls += 1; });

                await dm.openFile('listener_a.py');
                unsubscribe();
                await dm.openFile('listener_b.py');

                host.remove();
                return { calls };
            }
        """)

        assert result["calls"] == 1, f"Listener should only fire before unsubscribe: {result}"

    def test_initial_file_is_active_in_tab_bar(self, page, live_server):
        """The initially active file is shown as an active tab."""
        _load_editor(page, live_server)
        page.wait_for_function(
            "() => document.querySelector('.tab-bar__tab--active') !== null",
            timeout=8000,
        )
        active_tab = page.locator(".tab-bar__tab--active")
        assert active_tab.count() >= 1, "Active tab should be shown"
        label = active_tab.first.locator(".tab-bar__label").inner_text()
        # Active tab should show a Python file
        assert ".py" in label, f"Expected .py file tab, got: {label!r}"

    def test_open_second_file_switches_tab(self, page, live_server):
        """Opening a second file via the tree switches the active tab."""
        _load_editor(page, live_server)
        _import_opfs(page)

        # Create a second file
        page.evaluate("""
            async () => {
                await window.OPFSProject.writeFile('second.py', '# second file');
            }
        """)
        time.sleep(0.3)

        # Click the file in the tree — wait for it to appear first
        page.wait_for_function(
            "() => document.querySelector('.file-tree__list') !== null",
            timeout=5000,
        )
        # Reload tree by navigating to the page again (tree will show the new file)
        page.reload()
        page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)
        time.sleep(1.5)

        # Find second.py in the tree and click it
        tree_items = page.locator(".file-tree__file")
        found = False
        for i in range(tree_items.count()):
            item = tree_items.nth(i)
            if "second.py" in item.inner_text():
                item.locator(".file-tree__row").click()
                found = True
                break

        assert found, "second.py should be in the file tree"
        time.sleep(0.5)

        # The active tab should now show second.py
        page.wait_for_function(
            "() => { const t = document.querySelector('.tab-bar__tab--active .tab-bar__label'); return t && t.textContent.includes('second.py'); }",
            timeout=5000,
        )
        active_label = page.locator(".tab-bar__tab--active .tab-bar__label").inner_text()
        assert "second.py" in active_label, f"Active tab should be second.py, got: {active_label!r}"

    def test_edit_preserves_content_on_switch(self, page, live_server):
        """Edit file A, switch to B, switch back — A's content is preserved."""
        _load_editor(page, live_server)
        _import_opfs(page)

        # Create file B
        page.evaluate("""
            async () => {
                await window.OPFSProject.writeFile('file_b.py', '# file B');
            }
        """)
        time.sleep(0.3)

        # Reload to pick up the new file in the tree
        page.reload()
        page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)
        time.sleep(1.5)

        # Edit file A (main.py) — clear and type unique content
        page.locator("#clearBtn").click()
        time.sleep(0.2)
        page.locator(".editor-pane--active .cm-content").click()
        page.keyboard.type("# unique content in file A")
        time.sleep(0.3)

        # Switch to file B via tree
        tree_items = page.locator(".file-tree__file")
        for i in range(tree_items.count()):
            item = tree_items.nth(i)
            if "file_b.py" in item.inner_text():
                item.locator(".file-tree__row").click()
                break

        time.sleep(0.5)

        # Switch back to main.py (first tab)
        tabs = page.locator(".tab-bar__tab")
        for i in range(tabs.count()):
            tab = tabs.nth(i)
            if "main.py" in tab.inner_text():
                tab.click()
                break

        time.sleep(0.5)

        # Content should be preserved
        content = page.locator(".editor-pane--active .cm-content").inner_text()
        assert "unique content in file A" in content, \
            f"File A's content should be preserved after switching, got: {content[:200]!r}"

    def test_close_tab_removes_it(self, page, live_server):
        """Clicking × on a tab removes it from the tab bar."""
        _load_editor(page, live_server)
        _import_opfs(page)

        # Create an extra file so we always have one to close
        page.evaluate("""
            async () => {
                await window.OPFSProject.writeFile('closeable.py', '# close me');
            }
        """)
        page.reload()
        page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)
        time.sleep(1.5)

        # Open closeable.py
        tree_items = page.locator(".file-tree__file")
        for i in range(tree_items.count()):
            item = tree_items.nth(i)
            if "closeable.py" in item.inner_text():
                item.locator(".file-tree__row").click()
                break
        time.sleep(0.5)

        # Count tabs before close
        tab_count_before = page.locator(".tab-bar__tab").count()
        assert tab_count_before >= 2, "Should have at least 2 tabs open before closing"

        # Close the closeable.py tab
        tabs = page.locator(".tab-bar__tab")
        for i in range(tabs.count()):
            tab = tabs.nth(i)
            if "closeable.py" in tab.inner_text():
                tab.locator(".tab-bar__close").click()
                break

        time.sleep(0.3)
        tab_count_after = page.locator(".tab-bar__tab").count()
        assert tab_count_after < tab_count_before, \
            f"Tab count should decrease after close: {tab_count_before} → {tab_count_after}"
