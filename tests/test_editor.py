"""
Test suite for CodeMirror Python Editor
Tests the actual index.html page functionality using proper Playwright waits.

LSP-dependent tests are in test_lsp.py — this file only tests the editor UI.
"""

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.editor

# Timeout for CDN-loaded resources (CodeMirror modules from esm.sh)
CDN_TIMEOUT = 15_000


def _goto_editor(page, live_server):
    """Navigate to the editor and wait for CodeMirror to initialise."""
    page.goto(f"{live_server}/index.html")
    page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)


# ---------------------------------------------------------------------------
# Page structure
# ---------------------------------------------------------------------------


def test_page_loads(page, live_server):
    """Page loads and has the correct title."""
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("domcontentloaded")
    assert page.title() == "CodeMirror Python Editor"


def test_editor_container_exists(page, live_server):
    """Editor container element is present in the DOM."""
    _goto_editor(page, live_server)
    expect(page.locator("#editor-container")).to_be_visible()


def test_header_elements_present(page, live_server):
    """All header controls are rendered."""
    _goto_editor(page, live_server)

    expect(page.locator("header h1")).to_be_visible()
    assert page.locator("header h1").inner_text() == "CodeMirror 6 MicroPython Editor"

    expect(page.locator("#themeToggle")).to_be_visible()
    expect(page.locator("#typeCheckBtn")).to_be_visible()
    expect(page.locator("#clearBtn")).to_be_visible()
    expect(page.locator("#sampleSelect")).to_be_visible()
    expect(page.locator("#loadSampleBtn")).to_be_visible()


def test_footer_displays(page, live_server):
    """Footer and its documentation link are visible."""
    _goto_editor(page, live_server)
    expect(page.locator("footer")).to_be_visible()
    expect(page.locator("footer a")).to_be_visible()


# ---------------------------------------------------------------------------
# CodeMirror initialisation
# ---------------------------------------------------------------------------


def test_codemirror_editor_initializes(page, live_server):
    """CodeMirror editor, content area, and gutters are all rendered."""
    _goto_editor(page, live_server)

    expect(page.locator(".cm-editor")).to_be_visible()
    expect(page.locator(".cm-content")).to_be_visible()
    expect(page.locator(".cm-gutters")).to_be_visible()


def test_line_numbers_displayed(page, live_server):
    """Line-number gutter is visible and contains gutter elements."""
    _goto_editor(page, live_server)

    expect(page.locator(".cm-lineNumbers")).to_be_visible()
    assert page.locator(".cm-gutterElement").count() > 0, "Line number elements should exist"


def test_sample_code_loads(page, live_server):
    """Initial sample code (MicroPython blink example) is loaded."""
    _goto_editor(page, live_server)

    # Wait for real content — the placeholder is '# Loading example...'
    page.wait_for_function(
        "() => document.querySelector('.cm-content').innerText.includes('machine')",
        timeout=CDN_TIMEOUT,
    )
    content = page.locator(".cm-content").inner_text()
    assert "machine" in content, "Sample code should contain MicroPython imports"
    assert "def" in content, "Sample code should contain function definitions"


def test_python_syntax_highlighting(page, live_server):
    """Python syntax is highlighted — multiple .cm-line elements exist."""
    _goto_editor(page, live_server)

    # Wait for sample content
    page.wait_for_function(
        "() => document.querySelectorAll('.cm-line').length > 5",
        timeout=CDN_TIMEOUT,
    )
    expect(page.locator(".cm-line").first).to_be_visible()
    assert page.locator(".cm-line").count() > 5, "Sample code should produce multiple highlighted lines"


# ---------------------------------------------------------------------------
# Theme toggle
# ---------------------------------------------------------------------------


def test_initial_theme_is_light(page, live_server):
    """Page starts with the light theme applied."""
    _goto_editor(page, live_server)
    classes = page.locator("body").get_attribute("class") or ""
    assert "light-theme" in classes, f"Expected light-theme on body, got: {classes!r}"


def test_theme_toggle_switches_to_dark(page, live_server):
    """Clicking the theme toggle switches from light to dark."""
    _goto_editor(page, live_server)

    body = page.locator("body")
    assert "light-theme" in (body.get_attribute("class") or "")

    page.locator("#themeToggle").click()
    page.wait_for_function(
        "() => document.body.classList.contains('dark-theme')",
        timeout=5000,
    )
    classes = body.get_attribute("class") or ""
    assert "dark-theme" in classes, "Body should have dark-theme after toggle"


def test_theme_toggle_cycles_back_to_light(page, live_server):
    """Two theme toggles return to the original light theme."""
    _goto_editor(page, live_server)

    body = page.locator("body")
    page.locator("#themeToggle").click()
    page.wait_for_function("() => document.body.classList.contains('dark-theme')", timeout=5000)
    page.locator("#themeToggle").click()
    page.wait_for_function("() => document.body.classList.contains('light-theme')", timeout=5000)
    assert "light-theme" in (body.get_attribute("class") or "")


# ---------------------------------------------------------------------------
# Editor interactions
# ---------------------------------------------------------------------------


def test_clear_button_empties_editor(page, live_server):
    """Clear button removes all content from the editor."""
    _goto_editor(page, live_server)

    # Wait for sample to load
    page.wait_for_function(
        "() => document.querySelector('.cm-content').innerText.trim().length > 0",
        timeout=CDN_TIMEOUT,
    )

    page.locator("#clearBtn").click()

    page.wait_for_function(
        "() => document.querySelector('.cm-content').innerText.trim() === ''",
        timeout=5000,
    )
    assert page.locator(".cm-content").inner_text().strip() == "", "Editor should be empty after clear"


def test_editor_accepts_keyboard_input(page, live_server):
    """Typed text appears in the editor content."""
    _goto_editor(page, live_server)

    page.locator("#clearBtn").click()
    page.wait_for_function(
        "() => document.querySelector('.cm-content').innerText.trim() === ''",
        timeout=5000,
    )

    page.locator(".cm-content").click()
    test_text = "print('Hello, MicroPython!')"
    page.keyboard.type(test_text)

    page.wait_for_function(
        f"() => document.querySelector('.cm-content').innerText.includes(\"Hello, MicroPython!\")",
        timeout=5000,
    )
    assert "Hello, MicroPython!" in page.locator(".cm-content").inner_text()


def test_sample_selector_populated(page, live_server):
    """Example select dropdown is populated with at least one option after init."""
    _goto_editor(page, live_server)

    # Wait for JS to populate the select with example options
    page.wait_for_function(
        "() => document.getElementById('sampleSelect').options.length > 1",
        timeout=CDN_TIMEOUT,
    )
    option_count = page.evaluate("() => document.getElementById('sampleSelect').options.length")
    assert option_count > 1, "sampleSelect should have example options beyond the placeholder"


def test_load_sample_button_loads_code(page, live_server):
    """Load button replaces editor content with the selected sample."""
    _goto_editor(page, live_server)

    # Wait for selector to be populated
    page.wait_for_function(
        "() => document.getElementById('sampleSelect').options.length > 1",
        timeout=CDN_TIMEOUT,
    )

    # Clear the editor first
    page.locator("#clearBtn").click()
    page.wait_for_function(
        "() => document.querySelector('.cm-content').innerText.trim() === ''",
        timeout=5000,
    )

    # Select the first real option (index 1 skips the placeholder)
    page.evaluate("() => { const s = document.getElementById('sampleSelect'); s.selectedIndex = 1; }")

    page.locator("#loadSampleBtn").click()

    page.wait_for_function(
        "() => document.querySelector('.cm-content').innerText.trim().length > 0",
        timeout=CDN_TIMEOUT,
    )
    content = page.locator(".cm-content").inner_text()
    assert len(content.strip()) > 0, "Editor should contain code after loading sample"
    assert any(kw in content for kw in ("def", "import", "from", "#")), "Loaded sample should contain Python code"


# ---------------------------------------------------------------------------
# Responsive layout
# ---------------------------------------------------------------------------


def test_responsive_layout_desktop(page, live_server):
    """Editor container is visible at desktop resolution."""
    page.set_viewport_size({"width": 1920, "height": 1080})
    _goto_editor(page, live_server)
    expect(page.locator("#editor-container")).to_be_visible()


def test_responsive_layout_mobile(page, live_server):
    """Editor container and header are visible at mobile resolution."""
    page.set_viewport_size({"width": 375, "height": 667})
    _goto_editor(page, live_server)
    expect(page.locator("#editor-container")).to_be_visible()
    expect(page.locator("header")).to_be_visible()
