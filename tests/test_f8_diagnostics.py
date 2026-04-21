"""
Tests for F8 / Shift-F8 diagnostic navigation (nextDiagnostic / previousDiagnostic).

These tests inject diagnostics via setDiagnostics() and verify that
F8 opens the lint panel. No LSP worker is required.
"""

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.editor

CDN_TIMEOUT = 15_000


def _goto_editor(page, live_server):
    """Navigate to the editor and wait for CodeMirror to initialise."""
    page.goto(f"{live_server}/index.html")
    page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)


def _inject_diagnostics(page):
    """Inject a synthetic diagnostic into the editor via setDiagnostics."""
    page.evaluate("""async () => {
        const { EditorView } = await import('@codemirror/view');
        const { setDiagnostics } = await import('@codemirror/lint');
        const dom = document.querySelector('.cm-editor');
        const view = EditorView.findFromDOM(dom);
        view.dispatch(setDiagnostics(view.state, [
            {
                from: 0,
                to: 5,
                severity: 'error',
                message: 'Test error: undefined variable',
                source: 'test'
            }
        ]));
        return true;
    }""")


def test_f8_opens_lint_panel(page, live_server):
    """Pressing F8 with diagnostics present must open the lint panel."""
    _goto_editor(page, live_server)

    _inject_diagnostics(page)

    page.locator(".cm-content").click()
    page.keyboard.press("F8")

    panel = page.locator(".cm-panel.cm-panel-lint")
    expect(panel).to_be_visible(timeout=5000)


def test_lint_panel_shows_diagnostic_message(page, live_server):
    """The lint panel opened by F8 must display the diagnostic message."""
    _goto_editor(page, live_server)

    _inject_diagnostics(page)

    page.locator(".cm-content").click()
    page.keyboard.press("F8")

    panel = page.locator(".cm-panel.cm-panel-lint")
    expect(panel).to_be_visible(timeout=5000)

    expect(panel).to_contain_text("Test error: undefined variable")


def test_f8_without_diagnostics_does_not_crash(page, live_server):
    """Pressing F8 without diagnostics must not cause errors."""
    _goto_editor(page, live_server)

    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))

    page.locator(".cm-content").click()
    page.keyboard.press("F8")

    assert not errors, f"Unexpected JS errors: {errors}"
