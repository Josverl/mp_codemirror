"""
LSP Real-Time Diagnostics Tests

These tests verify that the browser's CodeMirror editor receives live
diagnostics from the Pyright Web Worker as the user types, including:
  - didChange notifications being sent and debounced
  - version counter incrementing correctly
  - diagnostics being updated when code changes

All tests require the Pyright worker bundle at dist/worker.js.
"""

import re
import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module-level skip marker
# ---------------------------------------------------------------------------

_worker_available = (Path(__file__).parent.parent / "dist" / "worker.js").exists()

requires_lsp = pytest.mark.skipif(
    not _worker_available,
    reason="Worker bundle not found at dist/worker.js. Build it first.",
)

pytestmark = pytest.mark.worker

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EDITOR_TIMEOUT = 15_000
LSP_TIMEOUT = 20_000
DEBOUNCE_MS = 300  # must match CHANGE_DEBOUNCE_MS in app.js


def _load_and_wait(page, base_url: str):
    """Navigate to editor and wait for LSP to initialise."""
    page.goto(f"{base_url}/index.html")
    page.wait_for_selector(".cm-editor", timeout=EDITOR_TIMEOUT)
    page.wait_for_function(
        "() => window.__lspReady === true || window.__lspFailed === true",
        timeout=15000
    )


def _clear_editor(page):
    page.locator("#clearBtn").click()
    time.sleep(0.3)


def _type_in_editor(page, text: str, delay: int = 50):
    editor = page.locator(".cm-content[contenteditable='true']")
    editor.click()
    editor.press_sequentially(text, delay=delay)


# ---------------------------------------------------------------------------
# Real-time diagnostics tests
# ---------------------------------------------------------------------------


@requires_lsp
def test_lsp_server_connects_via_browser(page, live_server):
    """Browser must log a successful transport connection and LSP handshake."""
    console: list[str] = []
    page.on("console", lambda m: console.append(m.text))

    _load_and_wait(page, live_server)

    transport_connected = any(
        "Transport connected" in m for m in console
    )
    lsp_ready = any("LSP client ready" in m for m in console)

    assert transport_connected, (
        f"Transport connection message not found. Console: {console[:15]}"
    )
    assert lsp_ready, (
        f"'LSP client ready' not found in console. Console: {console[:15]}"
    )


@requires_lsp
def test_did_change_notification_sent_on_typing(page, live_server):
    """Editing the document must trigger a didChange notification to the LSP."""
    console: list[str] = []
    page.on("console", lambda m: console.append(m.text))

    _load_and_wait(page, live_server)

    _clear_editor(page)
    console.clear()

    _type_in_editor(page, "import nonexistent_module")
    # Wait for debounce + a small margin
    time.sleep((DEBOUNCE_MS + 500) / 1000)

    didchange_msgs = [m for m in console if "didChange notification" in m]
    assert didchange_msgs, (
        f"Expected 'didChange notification' in console after typing. "
        f"Console: {[m for m in console if 'did' in m.lower()]}"
    )


@requires_lsp
def test_diagnostics_received_for_invalid_import(page, live_server):
    """Invalid import statement must result in diagnostics being received."""
    console: list[str] = []
    page.on("console", lambda m: console.append(m.text))

    _load_and_wait(page, live_server)

    _clear_editor(page)
    console.clear()

    _type_in_editor(page, "import nonexistent_module_xyz")

    # Wait for debounce + Pyright round-trip
    deadline = time.time() + LSP_TIMEOUT / 1000
    while time.time() < deadline:
        if any("Received diagnostics" in m for m in console):
            break
        time.sleep(0.5)

    assert any("Received diagnostics" in m for m in console), (
        "Pyright must push diagnostics after an invalid import. "
        f"Console: {[m for m in console if 'diagnostic' in m.lower()]}"
    )


@requires_lsp
def test_lint_marker_appears_in_gutter_on_typing(page, live_server):
    """Typing invalid code must cause a lint marker to appear in the gutter."""
    _load_and_wait(page, live_server)

    _clear_editor(page)
    _type_in_editor(page, "result = undefined_var_abc")

    marker = page.locator(".cm-lint-marker")
    marker.first.wait_for(timeout=LSP_TIMEOUT)
    assert marker.count() > 0, "Lint marker must appear after typing invalid code"


@requires_lsp
def test_did_change_is_debounced(page, live_server):
    """Rapid typing must produce at most a few didChange notifications, not one per key."""
    console: list[str] = []
    page.on("console", lambda m: console.append(m.text))

    _load_and_wait(page, live_server)

    _clear_editor(page)
    console.clear()

    # Type quickly (50 ms per key → 5 keys in ~250 ms, less than debounce window)
    _type_in_editor(page, "x = 1", delay=50)

    # Wait for the debounce window to flush
    time.sleep((DEBOUNCE_MS + 400) / 1000)

    didchange_count = sum(1 for m in console if "didChange notification" in m)
    assert didchange_count <= 2, (
        f"Debouncer must coalesce rapid keystrokes; got {didchange_count} notifications"
    )


@requires_lsp
def test_document_version_increments(page, live_server):
    """Each debounced change must increment the LSP document version."""
    console: list[str] = []
    page.on("console", lambda m: console.append(m.text))

    _load_and_wait(page, live_server)

    _clear_editor(page)
    console.clear()

    version_re = re.compile(r"version\s+(\d+)", re.IGNORECASE)

    # First edit
    _type_in_editor(page, "x = 1")
    time.sleep((DEBOUNCE_MS + 400) / 1000)

    # Second edit
    page.locator(".cm-content").press("Enter")
    _type_in_editor(page, "y = 2")
    time.sleep((DEBOUNCE_MS + 400) / 1000)

    versions = [
        int(m.group(1))
        for msg in console
        if "didChange notification" in msg
        for m in [version_re.search(msg)]
        if m
    ]

    assert len(versions) >= 1, (
        f"At least one version number must be logged. Console: "
        f"{[m for m in console if 'didChange' in m]}"
    )
    if len(versions) > 1:
        assert versions[-1] > versions[0], (
            f"Version must strictly increase: {versions}"
        )


@requires_lsp
def test_diagnostics_update_when_code_fixed(page, live_server):
    """Replacing invalid code with valid code must trigger a new diagnostics push."""
    console: list[str] = []
    page.on("console", lambda m: console.append(m.text))

    _load_and_wait(page, live_server)

    _clear_editor(page)
    console.clear()

    # Step 1: introduce an error
    _type_in_editor(page, "x = totally_undefined")
    deadline = time.time() + LSP_TIMEOUT / 1000
    while time.time() < deadline:
        if any("Received diagnostics" in m for m in console):
            break
        time.sleep(0.5)

    assert any("Received diagnostics" in m for m in console), (
        "Should receive diagnostics for invalid code first"
    )
    console.clear()

    # Step 2: use the Clear button, then type valid code
    _clear_editor(page)
    _type_in_editor(page, "x: int = 42")

    deadline = time.time() + LSP_TIMEOUT / 1000
    while time.time() < deadline:
        if any("Received diagnostics" in m for m in console):
            break
        time.sleep(0.5)

    assert any("Received diagnostics" in m for m in console), (
        "Pyright must push updated diagnostics after fixing the code"
    )
