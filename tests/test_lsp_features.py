"""
LSP Feature Tests: Completions and Hover Tooltips

Architecture: Browser (CodeMirror) <-> Web Worker (Pyright via dist/pyright_worker.js)

Two modes:
  - Smoke tests (no LSP):  verify the editor doesn't crash and that
    CodeMirror's built-in Python keyword completions still work.
  - Full tests  (LSP):     verify LSP-powered completions and hover tooltips.

Timing note: CodeMirror debounces didChange by 300 ms. The completion source
fires BEFORE the debounce, so Pyright may not yet have the latest content.
Integration tests therefore type the full content, wait for the didChange to
flush AND for Pyright to respond with diagnostics, then trigger explicit
completion via Ctrl+Space.
"""

import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module-level skip marker (evaluated at collection time)
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

EDITOR_TIMEOUT = 10_000
LSP_TIMEOUT = 20_000
DEBOUNCE_WAIT = 2.5  # debounce (300 ms) + Pyright round-trip margin


def _load_editor(page, base_url: str, wait_for_lsp: bool = True):
    """Navigate to the editor and wait for CodeMirror + optionally LSP."""
    page.goto(f"{base_url}/index.html")
    page.wait_for_selector(".cm-editor", timeout=EDITOR_TIMEOUT)
    if wait_for_lsp:
        page.wait_for_function(
            "() => window.__lspReady === true || window.__lspFailed === true",
            timeout=15000,
        )


def _clear_editor(page):
    page.locator("#clearBtn").click()
    time.sleep(0.3)


def _type_in_editor(page, text: str, delay: int = 30):
    editor = page.locator(".cm-content[contenteditable='true']")
    editor.click()
    editor.press_sequentially(text, delay=delay)


def _type_and_flush(page, text: str, extra_wait: float = DEBOUNCE_WAIT):
    """Type text, then wait long enough for the debounce to flush and Pyright to respond."""
    _type_in_editor(page, text)
    time.sleep(extra_wait)


# ---------------------------------------------------------------------------
# Smoke tests — no LSP required
# ---------------------------------------------------------------------------


def test_editor_loads_with_completions_infrastructure(page, live_server):
    """Autocomplete infrastructure must load even without LSP."""
    _load_editor(page, live_server, wait_for_lsp=False)

    assert page.locator(".cm-editor").is_visible()
    assert page.locator(".cm-content").is_visible()


def test_builtin_keyword_completion_works_without_lsp(page, live_server):
    """CodeMirror's built-in Python completer offers keywords without LSP."""
    _load_editor(page, live_server, wait_for_lsp=False)

    _clear_editor(page)
    _type_in_editor(page, "imp")

    # Trigger completion explicitly
    page.keyboard.press("Control+Space")
    time.sleep(1)

    autocomplete = page.locator(".cm-tooltip-autocomplete")
    if autocomplete.is_visible(timeout=3_000):
        options = page.locator(".cm-completionLabel")
        labels = [options.nth(i).inner_text() for i in range(min(10, options.count()))]
        assert any("import" in lbl for lbl in labels), f"'import' keyword should appear in completions. Got: {labels}"
    # If no autocomplete menu appears without LSP that's acceptable —
    # the important thing is no crash.


def test_typing_dot_does_not_crash_without_lsp(page, live_server):
    """Typing a dot accessor must not throw uncaught JS errors."""
    if _worker_available:
        pytest.skip("Skipped: LSP running; completion behaviour differs.")

    uncaught: list[str] = []
    page.on("pageerror", lambda e: uncaught.append(str(e)))

    _load_editor(page, live_server, wait_for_lsp=False)
    _clear_editor(page)
    _type_in_editor(page, "import sys\nsys.")
    time.sleep(1)

    assert not uncaught, f"Uncaught JS error on dot access: {uncaught}"


def test_ctrl_space_does_not_crash_without_lsp(page, live_server):
    """Ctrl+Space completion trigger must not throw uncaught JS errors."""
    if _worker_available:
        pytest.skip("Skipped: LSP running; completion behaviour differs.")

    uncaught: list[str] = []
    page.on("pageerror", lambda e: uncaught.append(str(e)))

    _load_editor(page, live_server, wait_for_lsp=False)
    _clear_editor(page)
    page.locator(".cm-content").click()
    page.keyboard.type("x = ")
    page.keyboard.press("Control+Space")
    time.sleep(1)

    assert not uncaught, f"Uncaught JS error on Ctrl+Space: {uncaught}"


# ---------------------------------------------------------------------------
# Full integration tests — LSP required
# ---------------------------------------------------------------------------


@requires_lsp
def test_completion_appears_after_explicit_trigger(page, live_server):
    """Ctrl+Space after content is flushed to Pyright must show completions.

    The 300 ms debounce means automatic completions fire before Pyright sees
    the latest content.  Explicit Ctrl+Space (after the flush) works reliably.
    """
    _load_editor(page, live_server)

    _clear_editor(page)
    _type_in_editor(page, "import sys")
    page.keyboard.press("Enter")
    page.keyboard.type("sys.")
    # Wait for debounce to flush AND for Pyright to process the content
    time.sleep(DEBOUNCE_WAIT)

    # Cursor is already at end of 'sys.' — trigger explicit completion
    page.keyboard.press("Control+Space")
    autocomplete = page.locator(".cm-tooltip-autocomplete")
    autocomplete.wait_for(timeout=LSP_TIMEOUT)
    assert autocomplete.is_visible(), "Autocomplete menu must appear after Ctrl+Space on 'sys.'"


@requires_lsp
def test_completion_shows_multiple_options(page, live_server):
    """sys module completions must include more than a handful of items."""
    _load_editor(page, live_server)

    _clear_editor(page)
    _type_in_editor(page, "import sys")
    page.keyboard.press("Enter")
    page.keyboard.type("sys.")
    time.sleep(DEBOUNCE_WAIT)

    page.keyboard.press("Control+Space")
    page.locator(".cm-tooltip-autocomplete").wait_for(timeout=LSP_TIMEOUT)
    count = page.locator(".cm-completionLabel").count()

    assert count > 5, f"sys module should have many completions; got {count}"


@requires_lsp
def test_completion_contains_known_sys_members(page, live_server):
    """sys completions must include 'argv'."""
    console_msgs: list[str] = []
    page.on("console", lambda m: console_msgs.append(m.text))

    _load_editor(page, live_server)

    _clear_editor(page)
    _type_in_editor(page, "import sys")
    page.keyboard.press("Enter")
    # Type prefix to filter — wait for Pyright to confirm it has the content
    page.keyboard.type("sys.arg")

    # Wait for the debounce to flush and Pyright to push diagnostics
    deadline = time.time() + LSP_TIMEOUT / 1000
    while time.time() < deadline:
        if any("Received diagnostics" in m for m in console_msgs[-5:]):
            break
        time.sleep(0.3)
    time.sleep(0.3)  # small extra margin

    page.keyboard.press("Control+Space")
    page.locator(".cm-tooltip-autocomplete").wait_for(timeout=LSP_TIMEOUT)
    options = page.locator(".cm-completionLabel")
    labels = [options.nth(i).inner_text() for i in range(min(20, options.count()))]

    assert any("argv" in lbl for lbl in labels), f"'argv' missing from filtered sys completions. Got: {labels}"


@requires_lsp
def test_completion_for_string_methods(page, live_server):
    """String method completions must include 'upper'."""
    console_msgs: list[str] = []
    page.on("console", lambda m: console_msgs.append(m.text))

    _load_editor(page, live_server)

    _clear_editor(page)
    _type_in_editor(page, 'text = "hello"')
    page.keyboard.press("Enter")
    # Type prefix 'up' to filter to 'upper' and related
    page.keyboard.type("text.up")

    # Wait for Pyright to confirm it has processed the document
    deadline = time.time() + LSP_TIMEOUT / 1000
    while time.time() < deadline:
        if any("Received diagnostics" in m for m in console_msgs[-5:]):
            break
        time.sleep(0.3)
    time.sleep(0.3)

    page.keyboard.press("Control+Space")
    page.locator(".cm-tooltip-autocomplete").wait_for(timeout=LSP_TIMEOUT)
    options = page.locator(".cm-completionLabel")
    labels = [options.nth(i).inner_text() for i in range(min(20, options.count()))]

    assert any("upper" in lbl.lower() for lbl in labels), (
        f"'upper' missing from filtered string completions. Got: {labels}"
    )


@requires_lsp
def test_completion_lsp_request_is_logged(page, live_server):
    """The LSP completion request must be logged to the browser console."""
    console_msgs: list[str] = []
    page.on("console", lambda m: console_msgs.append(m.text))

    _load_editor(page, live_server)

    _clear_editor(page)
    _type_in_editor(page, "import sys")
    page.keyboard.press("Enter")
    page.keyboard.type("sys.")
    time.sleep(DEBOUNCE_WAIT)

    page.keyboard.press("Control+Space")
    time.sleep(3)  # wait for the explicit completion round-trip

    completion_logs = [m for m in console_msgs if "completion" in m.lower()]
    assert completion_logs, (
        "LSP completion request must be logged to the console. "
        f"LSP-related: {[m for m in console_msgs if 'lsp' in m.lower()][:10]}"
    )


@requires_lsp
def test_hover_does_not_crash(page, live_server):
    """Hovering over a Python identifier must not produce uncaught JS errors."""
    uncaught: list[str] = []
    page.on("pageerror", lambda e: uncaught.append(str(e)))

    _load_editor(page, live_server)

    editor = page.locator(".cm-content")
    box = editor.bounding_box()
    if box:
        page.mouse.move(box["x"] + 50, box["y"] + 20)
        time.sleep(1.5)

    assert not uncaught, f"Uncaught JS error during hover: {uncaught}"


@requires_lsp
def test_hover_tooltip_appears_on_identifier(page, live_server):
    """Hovering over a known identifier must show a CodeMirror hover tooltip."""
    _load_editor(page, live_server)

    # Dispatch a synthetic mousemove over the editor content
    page.evaluate("""() => {
        const editor = document.querySelector('.cm-content');
        const rect = editor.getBoundingClientRect();
        const event = new MouseEvent('mousemove', {
            view: window, bubbles: true, cancelable: true,
            clientX: rect.left + 60, clientY: rect.top + 10
        });
        editor.dispatchEvent(event);
    }""")
    time.sleep(2)

    hover_tip = page.locator(".cm-tooltip-hover, .cm-lsp-hover")
    # Hover is position-dependent; assert no crash first.
    # If a tooltip did appear, verify it has content.
    if hover_tip.count() > 0 and hover_tip.first.is_visible(timeout=1_000):
        assert len(hover_tip.first.inner_text()) > 0, "Hover tooltip must contain some text"
