"""
Test suite for shareable links feature.

Tests URL encoding/decoding, share dropdown UI, and URL restoration.
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
# Share dropdown UI
# ---------------------------------------------------------------------------


def test_share_button_exists(page, live_server):
    """Share button is present in the header."""
    _goto_editor(page, live_server)
    expect(page.locator("#shareBtn")).to_be_visible()


def test_share_dropdown_hidden_by_default(page, live_server):
    """Share dropdown is hidden on page load."""
    _goto_editor(page, live_server)
    expect(page.locator("#shareDropdown")).to_be_hidden()


def test_share_dropdown_opens_on_click(page, live_server):
    """Clicking the Share button shows the dropdown."""
    _goto_editor(page, live_server)
    page.locator("#shareBtn").click()
    expect(page.locator("#shareDropdown")).to_be_visible()


def test_share_dropdown_has_three_options(page, live_server):
    """Dropdown contains the three copy options."""
    _goto_editor(page, live_server)
    page.locator("#shareBtn").click()
    expect(page.locator("#copyLink")).to_be_visible()
    expect(page.locator("#copyMdLink")).to_be_visible()
    expect(page.locator("#copyMdCode")).to_be_visible()


def test_share_dropdown_closes_on_outside_click(page, live_server):
    """Clicking outside the dropdown closes it."""
    _goto_editor(page, live_server)
    page.locator("#shareBtn").click()
    expect(page.locator("#shareDropdown")).to_be_visible()

    # Click elsewhere on the page
    page.locator("main").click()
    expect(page.locator("#shareDropdown")).to_be_hidden()


def test_share_dropdown_closes_on_escape(page, live_server):
    """Pressing Escape closes the dropdown."""
    _goto_editor(page, live_server)
    page.locator("#shareBtn").click()
    expect(page.locator("#shareDropdown")).to_be_visible()

    page.keyboard.press("Escape")
    expect(page.locator("#shareDropdown")).to_be_hidden()


def test_share_dropdown_toggles(page, live_server):
    """Clicking Share twice opens then closes the dropdown."""
    _goto_editor(page, live_server)
    page.locator("#shareBtn").click()
    expect(page.locator("#shareDropdown")).to_be_visible()
    page.locator("#shareBtn").click()
    expect(page.locator("#shareDropdown")).to_be_hidden()


# ---------------------------------------------------------------------------
# Compression roundtrip (tested in-browser via evaluate)
# ---------------------------------------------------------------------------


def test_compress_decompress_roundtrip(page, live_server):
    """Compressing and decompressing code yields the original text."""
    _goto_editor(page, live_server)

    result = page.evaluate("""async () => {
        const { compressCode, decompressCode } = await import('./share.js');
        const original = 'from machine import Pin\\nled = Pin(2, Pin.OUT)\\nled.on()';
        const compressed = await compressCode(original);
        const restored = await decompressCode(compressed);
        return { ok: restored === original, compressed, original, restored };
    }""")
    assert result["ok"], f"Roundtrip failed: {result['original']!r} != {result['restored']!r}"


def test_compress_empty_string(page, live_server):
    """Empty string compresses and decompresses correctly."""
    _goto_editor(page, live_server)

    result = page.evaluate("""async () => {
        const { compressCode, decompressCode } = await import('./share.js');
        const compressed = await compressCode('');
        const restored = await decompressCode(compressed);
        return restored === '';
    }""")
    assert result is True


def test_compress_unicode(page, live_server):
    """Unicode characters survive compression roundtrip."""
    _goto_editor(page, live_server)

    result = page.evaluate("""async () => {
        const { compressCode, decompressCode } = await import('./share.js');
        const original = '# Ünïcödé: 日本語 🐍';
        const compressed = await compressCode(original);
        const restored = await decompressCode(compressed);
        return restored === original;
    }""")
    assert result is True


# ---------------------------------------------------------------------------
# URL building
# ---------------------------------------------------------------------------


def test_build_shareable_url_contains_params(page, live_server):
    """buildShareableUrl produces a URL with board, typeCheckMode, and code params."""
    _goto_editor(page, live_server)

    result = page.evaluate("""async () => {
        const { buildShareableUrl } = await import('./share.js');
        const url = await buildShareableUrl('x = 1', 'esp32', 'strict');
        const parsed = new URL(url);
        return {
            board: parsed.searchParams.get('board'),
            typeCheckMode: parsed.searchParams.get('typeCheckMode'),
            hasCode: parsed.searchParams.has('code'),
        };
    }""")
    assert result["board"] == "esp32"
    assert result["typeCheckMode"] == "strict"
    assert result["hasCode"] is True


# ---------------------------------------------------------------------------
# URL restoration (shareable link loads code + settings)
# ---------------------------------------------------------------------------


def test_url_restores_code(page, live_server):
    """Loading a URL with code param restores the code in the editor."""
    # First get a compressed code value
    _goto_editor(page, live_server)
    compressed = page.evaluate("""async () => {
        const { compressCode } = await import('./share.js');
        return await compressCode('x = 42\\nprint(x)');
    }""")

    # Navigate to that shareable URL
    page.goto(f"{live_server}/index.html?code={compressed}")
    page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)

    content = page.evaluate("() => document.querySelector('.cm-content').innerText")
    assert "x = 42" in content
    assert "print(x)" in content


def test_url_restores_board(page, live_server):
    """Loading a URL with board param selects that board."""
    _goto_editor(page, live_server)
    compressed = page.evaluate("""async () => {
        const { compressCode } = await import('./share.js');
        return await compressCode('pass');
    }""")

    page.goto(f"{live_server}/index.html?board=esp32&code={compressed}")
    page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)

    board = page.evaluate("() => document.getElementById('boardSelect').value")
    assert board == "esp32"


def test_url_board_preloads_matching_stubs(page, live_server):
    """URL board selection must preload stubs for the same board before LSP init."""
    _goto_editor(page, live_server)
    compressed = page.evaluate("""async () => {
        const { compressCode } = await import('./share.js');
        return await compressCode('from machine import CAN');
    }""")

    page.goto(f"{live_server}/index.html?board=stm32&code={compressed}")
    page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)
    page.wait_for_function("() => document.getElementById('boardSelect').value === 'stm32'")

    page.wait_for_function(
        "() => performance.getEntriesByType('resource').some(e => e.name.includes('stubs-stm32.zip'))",
        timeout=5000,
    )
    fetched_resources = page.evaluate(
        "() => performance.getEntriesByType('resource').map(e => e.name)"
    )
    assert any("stubs-stm32.zip" in url for url in fetched_resources), (
        "Expected STM32 stubs to be fetched during URL-based board restore."
    )


def test_url_restores_typecheck_mode(page, live_server):
    """Loading a URL with typeCheckMode param selects that mode."""
    _goto_editor(page, live_server)
    compressed = page.evaluate("""async () => {
        const { compressCode } = await import('./share.js');
        return await compressCode('pass');
    }""")

    page.goto(f"{live_server}/index.html?typeCheckMode=strict&code={compressed}")
    page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)

    mode = page.evaluate("() => document.getElementById('typeCheckMode').value")
    assert mode == "strict"


def test_url_params_cleaned_after_restore(page, live_server):
    """After restoring from URL params, the address bar is cleaned up."""
    _goto_editor(page, live_server)
    compressed = page.evaluate("""async () => {
        const { compressCode } = await import('./share.js');
        return await compressCode('pass');
    }""")

    page.goto(f"{live_server}/index.html?code={compressed}")
    page.wait_for_selector(".cm-editor", timeout=CDN_TIMEOUT)

    # Wait for URL to be cleaned
    page.wait_for_function(
        "() => !window.location.search.includes('code=')",
        timeout=5000,
    )
    current_url = page.evaluate("() => window.location.href")
    assert "code=" not in current_url
