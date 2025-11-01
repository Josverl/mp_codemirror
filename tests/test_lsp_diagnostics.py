"""
Focused LSP Diagnostics Tests
Tests only the core LSP diagnostic functionality
"""
import time


def test_page_loads_with_lsp(page, live_server):
    """Test that page loads and LSP initializes"""
    page.goto(f"{live_server}/index.html")
    
    # Wait for editor to load
    page.wait_for_selector(".cm-editor", timeout=10000)
    
    # Verify editor is visible
    editor = page.locator(".cm-editor")
    assert editor.is_visible()


def test_diagnostic_icon_appears(page, live_server):
    """Test that diagnostic icon appears in gutter"""
    page.goto(f"{live_server}/index.html")
    page.wait_for_selector(".cm-editor", timeout=10000)
    
    # Wait for diagnostic marker to appear
    marker = page.locator(".cm-lint-marker-info")
    marker.wait_for(timeout=5000)
    
    assert marker.count() > 0, "Diagnostic marker should appear"
    assert marker.first.is_visible(), "Diagnostic marker should be visible"


def test_diagnostic_is_info_severity(page, live_server):
    """Test that diagnostic has correct info severity"""
    page.goto(f"{live_server}/index.html")
    page.wait_for_selector(".cm-editor", timeout=10000)
    
    # Mock sends info severity diagnostic
    info_marker = page.locator(".cm-lint-marker-info")
    info_marker.wait_for(timeout=5000)
    
    assert info_marker.is_visible(), "Info severity marker should be visible"
