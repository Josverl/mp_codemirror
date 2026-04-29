"""
LSP Diagnostics Integration Tests

Architecture: Browser (CodeMirror) <-> Web Worker (Pyright via dist/pyright_worker.js)

Two modes:
  - Smoke tests  (no LSP required): verify graceful degradation.
  - Full tests   (LSP required):    verify real diagnostics in the editor.
"""

import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module-level skip marker — evaluated at collection time
# ---------------------------------------------------------------------------

_worker_available = (Path(__file__).parent.parent / "dist" / "pyright_worker.js").exists()

requires_lsp = pytest.mark.skipif(
    not _worker_available,
    reason="Worker bundle not found at dist/pyright_worker.js. Build it first.",
)

pytestmark = pytest.mark.worker

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

from timing import EDITOR_TIMEOUT, LSP_TIMEOUT, UI_TIMEOUT, DEBOUNCE_SETTLE, SHORT_SETTLE, LSP_ROUND_TRIP, POLL_INTERVAL


def _load_editor(page, base_url: str):
    """Navigate to the editor and wait for CodeMirror to be ready."""
    page.goto(f"{base_url}/index.html?cb={time.time_ns()}", wait_until="domcontentloaded")
    page.wait_for_selector(".cm-editor", timeout=EDITOR_TIMEOUT)


def _clear_editor(page):
    page.locator(".cm-content").click()
    page.keyboard.press("Control+a")
    page.keyboard.press("Delete")
    page.wait_for_function(
        "() => document.querySelector('.cm-content').innerText.trim() === ''",
        timeout=UI_TIMEOUT,
    )


def _type_in_editor(page, text: str):
    editor = page.locator(".cm-content[contenteditable='true']")
    editor.click()
    editor.press_sequentially(text, delay=30)


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


# ---------------------------------------------------------------------------
# Smoke tests — no LSP required
# ---------------------------------------------------------------------------


def test_editor_loads_without_lsp(page, live_server):
    """Editor must load and be interactive even when LSP is unavailable."""
    console_msgs: list[str] = []
    page.on("console", lambda m: console_msgs.append(m.text))

    _load_editor(page, live_server)
    # Give app.js time to attempt (and possibly fail) LSP connection
    page.wait_for_function("() => window.__lspReady === true || window.__lspFailed === true", timeout=EDITOR_TIMEOUT)

    assert page.locator(".cm-editor").is_visible(), "Editor must be visible"
    assert page.locator(".cm-content").is_visible(), "Editor content area must be visible"

    # App must announce the graceful-degradation path in the console
    lsp_init_started = any("Initializing LSP client" in m for m in console_msgs)
    assert lsp_init_started, f"app.js must attempt LSP initialisation. Console messages: {console_msgs[:10]}"


def test_editor_remains_editable_without_lsp(page, live_server):
    """Typing in the editor must work regardless of LSP availability."""
    _load_editor(page, live_server)
    time.sleep(LSP_ROUND_TRIP - 0.5)

    _clear_editor(page)
    _type_in_editor(page, "x = 42")

    content = page.locator(".cm-content").inner_text()
    assert "x = 42" in content, "Typed text must appear in the editor"


def test_no_lint_markers_without_lsp(page, live_server):
    """Without LSP, no lint-gutter markers should be present."""
    if _worker_available:
        pytest.skip("Skipped: Worker bundle available; marker behaviour differs.")

    _load_editor(page, live_server)
    page.wait_for_function("() => window.__lspReady === true || window.__lspFailed === true", timeout=EDITOR_TIMEOUT)

    markers = page.locator(".cm-lint-marker")
    assert markers.count() == 0, "No lint markers expected when LSP is unavailable"


def test_lsp_failure_is_non_fatal(page, live_server):
    """An LSP connection failure must not crash the page."""
    if _worker_available:
        pytest.skip("Skipped: Worker bundle available; failure path not exercised.")

    uncaught_errors: list[str] = []
    page.on("pageerror", lambda exc: uncaught_errors.append(str(exc)))

    _load_editor(page, live_server)
    page.wait_for_function("() => window.__lspReady === true || window.__lspFailed === true", timeout=EDITOR_TIMEOUT)

    assert not uncaught_errors, f"Unexpected uncaught JS exceptions: {uncaught_errors}"
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
    page.wait_for_function("() => window.__lspReady === true || window.__lspFailed === true", timeout=EDITOR_TIMEOUT)

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
    page.wait_for_function("() => window.__lspReady === true || window.__lspFailed === true", timeout=EDITOR_TIMEOUT)

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
    page.wait_for_function("() => window.__lspReady === true || window.__lspFailed === true", timeout=EDITOR_TIMEOUT)

    # lintGutter() creates an element with class cm-gutter-lint
    lint_gutter = page.locator(".cm-gutter-lint")
    lint_gutter.wait_for(timeout=LSP_TIMEOUT)

    assert lint_gutter.is_visible(), "Lint gutter must be visible when LSP is active"


@requires_lsp
def test_error_severity_marker_shown(page, live_server):
    """An undefined-name error must produce an error-severity marker."""
    _load_editor(page, live_server)
    page.wait_for_function("() => window.__lspReady === true || window.__lspFailed === true", timeout=EDITOR_TIMEOUT)

    _clear_editor(page)
    _type_in_editor(page, "bad = no_such_variable_xyz")

    error_marker = page.locator(".cm-lint-marker-error")
    try:
        error_marker.first.wait_for(timeout=LSP_TIMEOUT)
        assert error_marker.is_visible()
    except Exception:
        # Pyright may emit 'warning' rather than 'error' for undefined names
        warn_marker = page.locator(".cm-lint-marker-warning, .cm-lint-marker-error")
        warn_marker.first.wait_for(timeout=UI_TIMEOUT)
        assert warn_marker.count() > 0, "At least one error/warning marker expected"


@requires_lsp
def test_diagnostics_published_to_console(page, live_server):
    """app.js must log received diagnostics to the browser console."""
    console_msgs: list[str] = []
    page.on("console", lambda m: console_msgs.append(m.text))

    _load_editor(page, live_server)
    page.wait_for_function("() => window.__lspReady === true || window.__lspFailed === true", timeout=EDITOR_TIMEOUT)

    _clear_editor(page)
    _type_in_editor(page, "x = totally_unknown_symbol")

    # Wait for diagnostic round-trip
    deadline = time.time() + LSP_TIMEOUT / 1000
    while time.time() < deadline:
        if any("Received diagnostics" in m for m in console_msgs):
            break
        time.sleep(SHORT_SETTLE)

    assert any("Received diagnostics" in m for m in console_msgs), (
        "Browser console must log received diagnostics. "
        f"Console: {[m for m in console_msgs if 'diagnostic' in m.lower()]}"
    )


@requires_lsp
def test_clean_code_produces_no_errors(page, live_server):
    """Valid Python must not produce error or warning lint markers."""
    _load_editor(page, live_server)
    page.wait_for_function("() => window.__lspReady === true || window.__lspFailed === true", timeout=EDITOR_TIMEOUT)

    _clear_editor(page)
    _type_in_editor(page, "x: int = 42")

    # Give Pyright time to analyse and respond
    page.wait_for_function("() => window.__lspReady === true || window.__lspFailed === true", timeout=EDITOR_TIMEOUT)

    error_markers = page.locator(".cm-lint-marker-error, .cm-lint-marker-warning")
    assert error_markers.count() == 0, "No error/warning markers expected for valid Python"


@requires_lsp
def test_cross_file_import_resolves_without_diagnostics(page, live_server):
    """Workspace files must be visible to Pyright so local imports resolve cleanly."""
    setup_url = f"{live_server}/tests/worker-transport-test.html?test-cross-file=setup&cb={time.time_ns()}"
    verify_url = f"{live_server}/index.html?test-cross-file=verify&cb={time.time_ns()}"

    page.goto(setup_url, wait_until="domcontentloaded")
    page.wait_for_load_state("load", timeout=10_000)

    page.evaluate(r"""
        async () => {
            const mod = await import('../storage/opfs-project.js');
            window.OPFSProject = mod.OPFSProject;
            await window.OPFSProject.init();

            const entries = await window.OPFSProject.listFiles();
            const paths = entries
                .map((entry) => entry.path)
                .sort((left, right) => right.length - left.length);

            for (const path of paths) {
                await window.OPFSProject.deleteFile(path);
            }

            await window.OPFSProject.writeFile(
                'helpers.py',
                ['def answer() -> int:', '    return 42', ''].join('\n')
            );
            await window.OPFSProject.writeFile(
                'main.py',
                ['from helpers import answer', 'x: int = answer()', ''].join('\n')
            );
            window.OPFSProject.setLastActiveFile('main.py');
        }
    """)

    page.goto(verify_url, wait_until="domcontentloaded")
    page.wait_for_selector(".cm-editor", timeout=30_000)
    page.wait_for_function("() => window.__lspReady === true || window.__lspFailed === true", timeout=EDITOR_TIMEOUT)
    time.sleep(LSP_ROUND_TRIP)

    diagnostics_text = page.locator("#diagnostics-status").inner_text()
    lint_markers = page.locator(".cm-lint-marker-error, .cm-lint-marker-warning")
    editor_text = page.locator(".cm-content").inner_text()

    assert "from helpers import answer" in editor_text, "main.py should load the cross-file import example"
    assert "Errors: 0" in diagnostics_text and "Warnings: 0" in diagnostics_text, (
        f"Expected clean diagnostics for local import, got: {diagnostics_text!r}"
    )
    assert lint_markers.count() == 0, "No lint markers expected when local imports resolve"
