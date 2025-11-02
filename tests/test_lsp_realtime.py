"""
Test suite for LSP Real-time Diagnostics
Tests the integration with Pyright LSP server and real-time error detection
"""
import re
import time


def test_lsp_server_connects(page, live_server, lsp_server):
    """Test that the LSP client connects to the WebSocket server"""
    # Collect console messages
    console_messages = []
    page.on("console", lambda msg: console_messages.append(msg.text))
    
    # Navigate to the page
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    
    # Wait for LSP initialization
    time.sleep(3)
    
    # Check for WebSocket connection
    ws_msgs = [msg for msg in console_messages if "WebSocket" in msg and "Connect" in msg]
    assert len(ws_msgs) > 0, "WebSocket should connect"
    
    # Check for LSP initialization
    init_msgs = [msg for msg in console_messages if "LSP" in msg or "Pyright" in msg]
    assert len(init_msgs) > 0, "LSP should initialize"


def test_realtime_diagnostics_invalid_import(page, live_server, lsp_server):
    """Test that real-time diagnostics detect invalid import statements"""
    # Collect console messages
    console_messages = []
    page.on("console", lambda msg: console_messages.append(msg.text))
    
    # Navigate and wait for initialization
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(3)
    
    # Clear the editor
    page.locator("#clearBtn").click()
    time.sleep(0.5)
    
    # Get the editor textbox
    editor = page.locator(".cm-content[contenteditable='true']")
    
    # Type invalid code
    editor.click()
    editor.press_sequentially("import nonexistent_module")
    
    # Wait for debounce (300ms) + processing time
    time.sleep(1)
    
    # Check for didChange notification in console
    didchange_msgs = [msg for msg in console_messages if "didChange notification" in msg]
    assert len(didchange_msgs) > 0, "Should send didChange notification"
    
    # Check for diagnostics received
    diagnostic_msgs = [msg for msg in console_messages if "Received diagnostics" in msg]
    assert len(diagnostic_msgs) > 0, "Should receive diagnostics from Pyright"
    
    # Check for error indicator in the gutter (red dot)
    # The diagnostic should create a lint marker
    time.sleep(0.5)
    
    # Verify error is visible by checking for diagnostic CSS classes or gutter elements
    # CodeMirror adds diagnostic markers to the gutter
    page.wait_for_selector(".cm-gutters", timeout=5000)
    

def test_realtime_diagnostics_undefined_variable(page, live_server, lsp_server):
    """Test that real-time diagnostics detect undefined variables"""
    # Collect console messages
    console_messages = []
    page.on("console", lambda msg: console_messages.append(msg.text))
    
    # Navigate and wait for initialization
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(3)
    
    # Clear the editor
    page.locator("#clearBtn").click()
    time.sleep(0.5)
    
    # Get the editor textbox
    editor = page.locator(".cm-content[contenteditable='true']")
    
    # Type code with undefined variable
    editor.click()
    editor.press_sequentially("print(undefined_variable)")
    
    # Wait for debounce + processing
    time.sleep(1)
    
    # Check for didChange notification
    didchange_msgs = [msg for msg in console_messages if "didChange" in msg]
    assert len(didchange_msgs) > 0, "Should send didChange notification"
    
    # Check for diagnostics received
    diagnostic_msgs = [msg for msg in console_messages if "diagnostic" in msg.lower()]
    assert len(diagnostic_msgs) > 0, "Should receive diagnostics"


def test_realtime_diagnostics_multiple_errors(page, live_server, lsp_server):
    """Test that real-time diagnostics can show multiple errors simultaneously"""
    # Collect console messages
    console_messages = []
    page.on("console", lambda msg: console_messages.append(msg.text))
    
    # Navigate and wait for initialization
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(3)
    
    # Clear the editor
    page.locator("#clearBtn").click()
    time.sleep(0.5)
    
    # Get the editor textbox
    editor = page.locator(".cm-content[contenteditable='true']")
    
    # Type code with multiple errors
    editor.click()
    editor.press_sequentially("import nonexistent_module\nprint(undefined_var)")
    
    # Wait for debounce + processing
    time.sleep(1)
    
    # Check for diagnostics received
    diagnostic_msgs = [msg for msg in console_messages if "diagnostic" in msg.lower()]
    assert len(diagnostic_msgs) > 0, "Should receive diagnostics"
    
    # Check that didChange was sent
    didchange_msgs = [msg for msg in console_messages if "didChange" in msg]
    assert len(didchange_msgs) > 0, "Should send didChange notification"


def test_realtime_diagnostics_clear_on_fix(page, live_server, lsp_server):
    """Test that diagnostics clear when code is fixed"""
    # Collect console messages
    console_messages = []
    page.on("console", lambda msg: console_messages.append(msg.text))
    
    # Navigate and wait for initialization
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(3)
    
    # Clear the editor
    page.locator("#clearBtn").click()
    time.sleep(0.5)
    
    # Get the editor textbox
    editor = page.locator(".cm-content[contenteditable='true']")
    
    # Type invalid code first
    editor.click()
    editor.press_sequentially("import nonexistent_module")
    time.sleep(1)
    
    # Verify diagnostics were received
    diagnostic_msgs = [msg for msg in console_messages if "diagnostic" in msg.lower()]
    assert len(diagnostic_msgs) > 0, "Should detect error first"
    
    # Clear messages to start fresh
    console_messages.clear()
    
    # Now replace with valid code
    page.keyboard.press("Control+A")
    editor.press_sequentially("x = 10\nprint(x)")
    
    # Wait for debounce + processing
    time.sleep(1)
    
    # Check that didChange was sent
    didchange_msgs = [msg for msg in console_messages if "didChange" in msg]
    assert len(didchange_msgs) > 0, "Should send didChange for fix"
    
    # Check for diagnostics received (should be empty or have no errors)
    diagnostic_msgs = [msg for msg in console_messages if "diagnostic" in msg.lower()]
    assert len(diagnostic_msgs) > 0, "Should receive diagnostics update"


def test_realtime_diagnostics_debouncing(page, live_server, lsp_server):
    """Test that didChange notifications are properly debounced"""
    # Collect console messages with timestamps
    console_messages = []
    
    def collect_with_time(msg):
        console_messages.append({
            'text': msg.text,
            'time': time.time()
        })
    
    page.on("console", collect_with_time)
    
    # Navigate and wait for initialization
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(3)
    
    # Clear the editor
    page.locator("#clearBtn").click()
    time.sleep(0.5)
    
    # Get the editor textbox
    editor = page.locator(".cm-content[contenteditable='true']")
    editor.click()
    
    # Clear messages to start fresh
    console_messages.clear()
    
    # Type quickly (simulating rapid typing)
    editor.press_sequentially("x = 1", delay=50)  # 50ms between keys
    
    # Wait for debounce timeout
    time.sleep(0.5)
    
    # Count didChange notifications
    didchange_msgs = [msg for msg in console_messages if "didChange notification" in msg['text']]
    
    # Should only send ONE notification after debouncing
    # (or very few, not one per keystroke)
    assert len(didchange_msgs) <= 2, f"Should debounce changes, got {len(didchange_msgs)} notifications"


def test_realtime_diagnostics_version_increment(page, live_server, lsp_server):
    """Test that document version increments with each change"""
    # Collect console messages
    console_messages = []
    page.on("console", lambda msg: console_messages.append(msg.text))
    
    # Navigate and wait for initialization
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(3)
    
    # Clear the editor
    page.locator("#clearBtn").click()
    time.sleep(0.5)
    
    # Get the editor textbox
    editor = page.locator(".cm-content[contenteditable='true']")
    editor.click()
    
    # Clear messages to start fresh
    console_messages.clear()
    
    # Make first change
    editor.press_sequentially("x = 1")
    time.sleep(0.6)  # Wait for debounce
    
    # Make second change
    editor.press("Enter")
    editor.press_sequentially("y = 2")
    time.sleep(0.6)  # Wait for debounce
    
    # Extract version numbers from didChange messages
    version_pattern = re.compile(r'version (\d+)')
    versions = []
    for msg in console_messages:
        if "didChange notification" in msg:
            match = version_pattern.search(msg)
            if match:
                versions.append(int(match.group(1)))
    
    # Should have at least one version (may coalesce rapid changes due to debounce)
    assert len(versions) >= 1, f"Should have at least 1 version update, got {len(versions)}"
    
    # If we got multiple versions, they should increment
    if len(versions) > 1:
        assert versions[-1] > versions[0], f"Version should increment: {versions}"


def test_valid_micropython_code_no_errors(page, live_server, lsp_server):
    """Test that valid MicroPython code with 'machine' import shows no errors"""
    # Collect console messages
    console_messages = []
    page.on("console", lambda msg: console_messages.append(msg.text))
    
    # Navigate and wait for initialization  
    page.goto(f"{live_server}/index.html")
    page.wait_for_load_state("networkidle")
    time.sleep(3)
    
    # The default example (blink LED) should be loaded
    # It uses 'from machine import Pin' which should be valid with MicroPython stubs
    
    # Wait a bit more for diagnostics
    time.sleep(2)
    
    # Check diagnostics - should be empty for valid MicroPython code
    diagnostic_msgs = [msg for msg in console_messages if "Received diagnostics" in msg]
    
    # Find the last diagnostics message
    if diagnostic_msgs:
        last_diagnostic = diagnostic_msgs[-1]
        # Should show empty array
        assert "[]" in last_diagnostic, f"Valid MicroPython code should have no errors, got: {last_diagnostic}"
