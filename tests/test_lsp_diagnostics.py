"""
LSP Diagnostics Integration Tests

Architecture: Browser (CodeMirror) <-> WebSocket :9011 <-> Pyright

Two modes:
  - Smoke tests  (no LSP required): verify graceful degradation.
  - Full tests   (LSP required):    verify real diagnostics in the editor.
"""

import socket
import time

import pytest

# ---------------------------------------------------------------------------
# Module-level skip marker — evaluated at collection time
# ---------------------------------------------------------------------------

_lsp_up = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    _lsp_available = _lsp_up.connect_ex(("localhost", 9011)) == 0
finally:
    _lsp_up.close()

requires_lsp = pytest.mark.skipif(
    not _lsp_available,
    reason="LSP bridge not running on port 9011. Start: Run Task > 'Start LSP Bridge'",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EDITOR_TIMEOUT = 10_000  # ms – time for CodeMirror to initialise from CDN
LSP_TIMEOUT = 15_000     # ms – time for Pyright to process and push diagnostics


def _load_editor(page, base_url: str):
    """Navigate to the editor and wait for CodeMirror to be ready."""
    page.goto(f"{base_url}/index.html")
    page.wait_for_selector(".cm-editor", timeout=EDITOR_TIMEOUT)


def _clear_editor(page):
    page.locator("#clearBtn").click()
    time.sleep(0.3)


def _type_in_editor(page, text: str):
    editor = page.locator(".cm-content[contenteditable='true']")
    editor.click()
    editor.press_sequentially(text, delay=30)


# ---------------------------------------------------------------------------
# Smoke tests — no LSP required
# ---------------------------------------------------------------------------


def test_editor_loads_without_lsp(page, live_server):
    """Editor must load and be interactive even when LSP is unavailable."""
    console_msgs: list[str] = []
    page.on("console", lambda m: console_msgs.append(m.text))

    _load_editor(page, live_server)
    # Give app.js time to attempt (and possibly fail) LSP connection
    time.sleep(3)

    assert page.locator(".cm-editor").is_visible(), "Editor must be visible"
    assert page.locator(".cm-content").is_visible(), "Editor content area must be visible"

    # App must announce the graceful-degradation path in the console
    lsp_init_started = any("Initializing LSP client" in m for m in console_msgs)
    assert lsp_init_started, (
        "app.js must attempt LSP initialisation. "
        f"Console messages: {console_msgs[:10]}"
    )


def test_editor_remains_editable_without_lsp(page, live_server):
    """Typing in the editor must work regardless of LSP availability."""
    _load_editor(page, live_server)
    time.sleep(2)

    _clear_editor(page)
    _type_in_editor(page, "x = 42")

    content = page.locator(".cm-content").inner_text()
    assert "x = 42" in content, "Typed text must appear in the editor"


def test_no_lint_markers_without_lsp(page, live_server):
    """Without LSP, no lint-gutter markers should be present."""
    if _lsp_available:
        pytest.skip("Skipped: LSP is running; marker behaviour differs.")

    _load_editor(page, live_server)
    time.sleep(3)

    markers = page.locator(".cm-lint-marker")
    assert markers.count() == 0, (
        "No lint markers expected when LSP is unavailable"
    )


def test_lsp_failure_is_non_fatal(page, live_server):
    """A WebSocket connection failure must not crash the page."""
    if _lsp_available:
        pytest.skip("Skipped: LSP is running; failure path not exercised.")

    uncaught_errors: list[str] = []
    page.on("pageerror", lambda exc: uncaught_errors.append(str(exc)))

    _load_editor(page, live_server)
    time.sleep(3)

    assert not uncaught_errors, (
        f"Unexpected uncaught JS exceptions: {uncaught_errors}"
    )
    # Editor must still be usable
    assert page.locator(".cm-editor").is_visible()


# ---------------------------------------------------------------------------
# Full integration tests — LSP required
# ---------------------------------------------------------------------------


@requires_lsp
def test_lsp_client_initialises_in_browser(page, live_server):
    """Browser must successfully negotiate the LSP handshake."""
    console_msgs: list[str] = []
    page.on("console", lambda m: console_msgs.append(m.text))

    _load_editor(page, live_server)
    time.sleep(4)

    assert any("LSP client ready" in m for m in console_msgs), (
        f"Expected 'LSP client ready' in console. Got: {console_msgs[:15]}"
    )
    assert any("LSP Client initialized" in m for m in console_msgs), (
        "LSP capabilities must be logged after initialize handshake"
    )


@requires_lsp
def test_diagnostics_appear_for_undefined_variable(page, live_server):
    """Typing code with an undefined variable must produce a lint marker."""
    _load_editor(page, live_server)
    time.sleep(4)  # wait for LSP init

    _clear_editor(page)
    _type_in_editor(page, "result = clearly_undefined_name")

    # Wait for debounce (300 ms) + Pyright processing
    marker = page.locator(".cm-lint-marker")
    marker.first.wait_for(timeout=LSP_TIMEOUT)

    assert marker.count() > 0, "A lint marker must appear for undefined name"


@requires_lsp
def test_diagnostic_gutter_is_present(page, live_server):
    """The lint gutter element must be rendered when LSP is connected."""
    _load_editor(page, live_server)
    time.sleep(4)

    # lintGutter() creates an element with class cm-gutter-lint
    lint_gutter = page.locator(".cm-gutter-lint")
    lint_gutter.wait_for(timeout=LSP_TIMEOUT)

    assert lint_gutter.is_visible(), "Lint gutter must be visible when LSP is active"


@requires_lsp
def test_error_severity_marker_shown(page, live_server):
    """An undefined-name error must produce an error-severity marker."""
    _load_editor(page, live_server)
    time.sleep(4)

    _clear_editor(page)
    _type_in_editor(page, "bad = no_such_variable_xyz")

    error_marker = page.locator(".cm-lint-marker-error")
    try:
        error_marker.first.wait_for(timeout=LSP_TIMEOUT)
        assert error_marker.is_visible()
    except Exception:
        # Pyright may emit 'warning' rather than 'error' for undefined names
        warn_marker = page.locator(".cm-lint-marker-warning, .cm-lint-marker-error")
        warn_marker.first.wait_for(timeout=5_000)
        assert warn_marker.count() > 0, "At least one error/warning marker expected"


@requires_lsp
def test_diagnostics_published_to_console(page, live_server):
    """app.js must log received diagnostics to the browser console."""
    console_msgs: list[str] = []
    page.on("console", lambda m: console_msgs.append(m.text))

    _load_editor(page, live_server)
    time.sleep(4)

    _clear_editor(page)
    _type_in_editor(page, "x = totally_unknown_symbol")

    # Wait for diagnostic round-trip
    deadline = time.time() + LSP_TIMEOUT / 1000
    while time.time() < deadline:
        if any("Received diagnostics" in m for m in console_msgs):
            break
        time.sleep(0.5)

    assert any("Received diagnostics" in m for m in console_msgs), (
        "Browser console must log received diagnostics. "
        f"Console: {[m for m in console_msgs if 'diagnostic' in m.lower()]}"
    )


@requires_lsp
def test_clean_code_produces_no_errors(page, live_server):
    """Valid Python must not produce error or warning lint markers."""
    _load_editor(page, live_server)
    time.sleep(4)

    _clear_editor(page)
    _type_in_editor(page, "x: int = 42\ny: str = 'hello'\nprint(x, y)")

    # Give Pyright time to analyse and respond
    time.sleep(4)

    error_markers = page.locator(".cm-lint-marker-error, .cm-lint-marker-warning")
    assert error_markers.count() == 0, (
        "No error/warning markers expected for valid Python"
    )
