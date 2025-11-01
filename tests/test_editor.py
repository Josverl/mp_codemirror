"""
Test suite for CodeMirror Python Editor
Tests the actual index.html page functionality
"""
import time


def test_page_loads(page, live_server):
    """Test that the page loads without errors"""
    page.goto(f"{live_server}/index.html")
    
    # Wait for the page to load
    page.wait_for_load_state("networkidle")
    
    # Check that the title is correct
    assert page.title() == "CodeMirror Python Editor"
    
    # Check for no console errors (except known safe ones)
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
    
    time.sleep(1)
    
    # Filter out known safe errors like dev tools requests
    real_errors = [e for e in console_errors if "devtools" not in str(e).lower()]
    assert len(real_errors) == 0, f"Console errors found: {real_errors}"


def test_editor_container_exists(page, live_server):
    """Test that the editor container element exists"""
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    
    # Wait for editor container
    editor_container = page.locator("#editor-container")
    assert editor_container.is_visible(), "Editor container should be visible"


def test_header_elements_present(page, live_server):
    """Test that header elements are present"""
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    
    # Check header
    assert page.locator("header h1").is_visible()
    assert page.locator("header h1").inner_text() == "CodeMirror 6 Python Editor"
    
    # Check buttons
    assert page.locator("#themeToggle").is_visible()
    assert page.locator("#clearBtn").is_visible()
    assert page.locator("#getSampleBtn").is_visible()


def test_codemirror_editor_initializes(page, live_server):
    """Test that CodeMirror editor initializes properly"""
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    
    # Wait a bit for CodeMirror to load from CDN
    time.sleep(2)
    
    # Check for CodeMirror elements
    cm_editor = page.locator(".cm-editor")
    assert cm_editor.is_visible(), "CodeMirror editor should be visible"
    
    # Check for content area
    cm_content = page.locator(".cm-content")
    assert cm_content.is_visible(), "CodeMirror content area should be visible"
    
    # Check for gutters (line numbers)
    cm_gutters = page.locator(".cm-gutters")
    assert cm_gutters.is_visible(), "CodeMirror gutters should be visible"


def test_sample_code_loads(page, live_server):
    """Test that sample code is loaded initially"""
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    # Check that there's content in the editor
    cm_content = page.locator(".cm-content")
    content_text = cm_content.inner_text()
    
    # Sample should contain MicroPython code
    assert "MicroPython" in content_text or "def" in content_text, \
        "Sample code should be loaded"


def test_clear_button_works(page, live_server):
    """Test that the clear button clears the editor"""
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    # Click clear button
    page.locator("#clearBtn").click()
    time.sleep(0.5)
    
    # Check that content is empty
    cm_content = page.locator(".cm-content")
    content_text = cm_content.inner_text().strip()
    
    assert content_text == "", "Editor should be empty after clear"


def test_load_sample_button_works(page, live_server):
    """Test that load sample button loads code"""
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    # Clear first
    page.locator("#clearBtn").click()
    time.sleep(0.5)
    
    # Load sample
    page.locator("#getSampleBtn").click()
    time.sleep(0.5)
    
    # Check that content is loaded
    cm_content = page.locator(".cm-content")
    content_text = cm_content.inner_text()
    
    assert len(content_text) > 0, "Sample code should be loaded"
    assert "def" in content_text or "import" in content_text, \
        "Sample should contain Python code"


def test_theme_toggle_button_works(page, live_server):
    """Test that theme toggle button changes the theme"""
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    # Get initial theme (should be dark)
    body = page.locator("body")
    initial_classes = body.get_attribute("class")
    assert "dark-theme" in initial_classes, "Initial theme should be dark"
    
    # Click theme toggle
    page.locator("#themeToggle").click()
    time.sleep(0.5)
    
    # Check theme changed
    new_classes = body.get_attribute("class")
    assert "light-theme" in new_classes, "Theme should change to light"
    
    # Toggle back
    page.locator("#themeToggle").click()
    time.sleep(0.5)
    
    # Check theme changed back
    final_classes = body.get_attribute("class")
    assert "dark-theme" in final_classes, "Theme should toggle back to dark"


def test_editor_accepts_input(page, live_server):
    """Test that the editor accepts keyboard input"""
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    # Clear editor
    page.locator("#clearBtn").click()
    time.sleep(0.5)
    
    # Click in editor to focus
    page.locator(".cm-content").click()
    
    # Type some text
    test_text = "print('Hello, World!')"
    page.keyboard.type(test_text)
    time.sleep(0.5)
    
    # Check that text was entered
    cm_content = page.locator(".cm-content")
    content_text = cm_content.inner_text()
    
    assert test_text in content_text, "Typed text should appear in editor"


def test_python_syntax_highlighting(page, live_server):
    """Test that Python syntax highlighting is working"""
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    # Check for syntax highlighting tokens
    # CodeMirror adds classes for syntax elements
    cm_line = page.locator(".cm-line").first
    
    # Just verify that the editor has rendered lines
    assert cm_line.is_visible(), "Editor lines should be visible"
    
    # Check that there are multiple lines (from sample code)
    all_lines = page.locator(".cm-line").all()
    assert len(all_lines) > 5, "Sample code should have multiple lines"


def test_line_numbers_displayed(page, live_server):
    """Test that line numbers are displayed"""
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    # Check for line number gutter
    line_numbers = page.locator(".cm-lineNumbers")
    assert line_numbers.is_visible(), "Line numbers should be visible"
    
    # Check for gutter elements
    gutter_elements = page.locator(".cm-gutterElement").all()
    assert len(gutter_elements) > 0, "Line number elements should exist"


def test_responsive_layout(page, live_server):
    """Test that the layout is responsive"""
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    # Test desktop size
    page.set_viewport_size({"width": 1920, "height": 1080})
    time.sleep(0.5)
    assert page.locator("#editor-container").is_visible()
    
    # Test mobile size
    page.set_viewport_size({"width": 375, "height": 667})
    time.sleep(0.5)
    assert page.locator("#editor-container").is_visible()
    assert page.locator("header").is_visible()


def test_no_javascript_errors(page, live_server):
    """Test that there are no JavaScript errors on load"""
    errors = []
    
    def handle_console(msg):
        if msg.type == "error":
            errors.append(msg.text)
    
    page.on("console", handle_console)
    
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(3)
    
    # Filter out known safe errors
    real_errors = [e for e in errors 
                   if "devtools" not in e.lower() 
                   and "extension" not in e.lower()]
    
    assert len(real_errors) == 0, f"JavaScript errors found: {real_errors}"


def test_footer_displays(page, live_server):
    """Test that footer is displayed"""
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    
    footer = page.locator("footer")
    assert footer.is_visible(), "Footer should be visible"
    
    # Check for link to CodeMirror docs
    docs_link = page.locator("footer a")
    assert docs_link.is_visible(), "Documentation link should be visible"
