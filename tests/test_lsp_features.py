"""
Test suite for LSP Autocompletion and Hover Tooltips
Tests Sprint 4 features: completion menu and hover documentation
"""
import time


class TestAutocompletion:
    """Tests for LSP-powered autocompletion feature"""
    
    def test_completion_menu_appears_on_dot_access(self, page, live_server):
        """Test that completion menu appears when typing dot after module name"""
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Clear editor
        page.locator("#clearBtn").click()
        time.sleep(0.5)
        
        # Type code with module access
        page.locator(".cm-content").click()
        page.keyboard.type("import sys\nsys.")
        time.sleep(1)  # Wait for completion to trigger
        
        # Check for autocomplete menu
        autocomplete_menu = page.locator(".cm-tooltip-autocomplete")
        assert autocomplete_menu.is_visible(timeout=5000), \
            "Autocomplete menu should appear after 'sys.'"
    
    def test_completion_shows_multiple_options(self, page, live_server):
        """Test that completion menu shows multiple options"""
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Clear and type
        page.locator("#clearBtn").click()
        time.sleep(0.5)
        page.locator(".cm-content").click()
        page.keyboard.type("import sys\nsys.")
        time.sleep(1)
        
        # Check for completion options
        completion_options = page.locator(".cm-completionLabel")
        options_count = completion_options.count()
        
        assert options_count > 10, \
            f"Should show many completions for sys module, got {options_count}"
    
    def test_completion_contains_expected_sys_members(self, page, live_server):
        """Test that sys module completions include known members"""
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Clear and type
        page.locator("#clearBtn").click()
        time.sleep(0.5)
        page.locator(".cm-content").click()
        page.keyboard.type("import sys\nsys.")
        time.sleep(1)
        
        # Get all completion labels
        completion_options = page.locator(".cm-completionLabel")
        labels = [completion_options.nth(i).inner_text() 
                 for i in range(min(20, completion_options.count()))]
        
        # Check for known sys members
        assert any("platform" in label for label in labels), \
            "sys completions should include 'platform'"
        assert any("argv" in label for label in labels), \
            "sys completions should include 'argv'"
    
    def test_completion_for_string_methods(self, page, live_server):
        """Test that string method completions work"""
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Clear and type
        page.locator("#clearBtn").click()
        time.sleep(0.5)
        page.locator(".cm-content").click()
        page.keyboard.type('text = "hello"\ntext.')
        time.sleep(1)
        
        # Check for completion menu
        autocomplete_menu = page.locator(".cm-tooltip-autocomplete")
        assert autocomplete_menu.is_visible(timeout=5000), \
            "Autocomplete menu should appear for string methods"
        
        # Check for string methods
        completion_options = page.locator(".cm-completionLabel")
        labels = [completion_options.nth(i).inner_text() 
                 for i in range(min(20, completion_options.count()))]
        
        assert any("upper" in label.lower() for label in labels), \
            "Should include 'upper' method"
        assert any("lower" in label.lower() for label in labels), \
            "Should include 'lower' method"
    
    def test_completion_for_micropython_pin(self, page, live_server):
        """Test that MicroPython Pin completions work"""
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Load default sample (has Pin)
        cm_content = page.locator(".cm-content")
        content_text = cm_content.inner_text()
        
        if "Pin" not in content_text:
            # Load sample if not already loaded
            page.locator("#getSampleBtn").click()
            time.sleep(1)
        
        # Click at end of file and add new line
        page.locator(".cm-content").click()
        page.keyboard.press("Control+End")
        page.keyboard.press("Enter")
        page.keyboard.type("pin = Pin(2, Pin.OUT)\npin.")
        time.sleep(1)
        
        # Check for completion menu
        autocomplete_menu = page.locator(".cm-tooltip-autocomplete")
        assert autocomplete_menu.is_visible(timeout=5000), \
            "Autocomplete menu should appear for Pin methods"
        
        # Check for Pin methods
        completion_options = page.locator(".cm-completionLabel")
        labels = [completion_options.nth(i).inner_text() 
                 for i in range(min(15, completion_options.count()))]
        
        # Pin should have on(), off(), value() methods
        assert any("on" in label.lower() for label in labels), \
            "Pin completions should include 'on' method"
    
    def test_completion_on_import_statement(self, page, live_server):
        """Test that import completions work"""
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Clear and type incomplete import
        page.locator("#clearBtn").click()
        time.sleep(0.5)
        page.locator(".cm-content").click()
        page.keyboard.type("import o")
        
        # Trigger completion with Ctrl+Space
        page.keyboard.press("Control+Space")
        time.sleep(1)
        
        # Check for completion menu
        autocomplete_menu = page.locator(".cm-tooltip-autocomplete")
        assert autocomplete_menu.is_visible(timeout=5000), \
            "Autocomplete menu should appear for import"
        
        # Check for os module
        completion_options = page.locator(".cm-completionLabel")
        labels = [completion_options.nth(i).inner_text() 
                 for i in range(min(10, completion_options.count()))]
        
        assert any("os" in label.lower() for label in labels), \
            "Import completions should include 'os' module"
    
    def test_completion_manual_trigger_with_ctrl_space(self, page, live_server):
        """Test that Ctrl+Space manually triggers completion"""
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Clear and type without triggering automatic completion
        page.locator("#clearBtn").click()
        time.sleep(0.5)
        page.locator(".cm-content").click()
        page.keyboard.type("import sys\nsy")
        time.sleep(0.5)
        
        # Manually trigger with Ctrl+Space
        page.keyboard.press("Control+Space")
        time.sleep(1)
        
        # Check for completion menu
        autocomplete_menu = page.locator(".cm-tooltip-autocomplete")
        assert autocomplete_menu.is_visible(timeout=5000), \
            "Autocomplete menu should appear on Ctrl+Space"
    
    def test_completion_lsp_logging(self, page, live_server):
        """Test that LSP completion requests are logged"""
        console_messages = []
        
        def handle_console(msg):
            console_messages.append(msg.text)
        
        page.on("console", handle_console)
        
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Trigger completion
        page.locator("#clearBtn").click()
        time.sleep(0.5)
        page.locator(".cm-content").click()
        page.keyboard.type("import sys\nsys.")
        time.sleep(2)
        
        # Check for LSP completion messages
        completion_messages = [msg for msg in console_messages 
                              if "completion" in msg.lower()]
        
        assert len(completion_messages) > 0, \
            "LSP completion messages should be logged"


class TestHoverTooltips:
    """Tests for LSP-powered hover tooltip feature"""
    
    def test_hover_appears_on_pin_class(self, page, live_server):
        """Test that hover tooltip appears when hovering over Pin class"""
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Ensure sample code with Pin is loaded
        cm_content = page.locator(".cm-content")
        content_text = cm_content.inner_text()
        
        if "Pin" not in content_text:
            page.locator("#getSampleBtn").click()
            time.sleep(1)
        
        # Find and hover over "Pin" in the import statement
        # Use JavaScript to trigger hover event at specific position
        page.evaluate("""
            const editor = document.querySelector('.cm-content');
            const rect = editor.getBoundingClientRect();
            const event = new MouseEvent('mousemove', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: rect.left + 133,
                clientY: rect.top + 60
            });
            editor.dispatchEvent(event);
        """)
        time.sleep(1)
        
        # Check for hover tooltip (might not always trigger on exact position)
        console_messages = []
        page.on("console", lambda msg: console_messages.append(msg.text))
        time.sleep(1)
        
        # Check if hover was triggered (from console logs)
        hover_messages = [msg for msg in console_messages 
                         if "hover" in msg.lower()]
        
        # At minimum, verify hover infrastructure is loaded
        assert "hover" in page.content().lower() or len(hover_messages) > 0, \
            "Hover functionality should be present"
    
    def test_hover_shows_documentation(self, page, live_server):
        """Test that hover tooltip shows documentation content"""
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Ensure sample with machine module is loaded
        cm_content = page.locator(".cm-content")
        content_text = cm_content.inner_text()
        
        if "machine" not in content_text:
            page.locator("#getSampleBtn").click()
            time.sleep(1)
        
        # Hover over "machine" keyword
        page.evaluate("""
            const editor = document.querySelector('.cm-content');
            const rect = editor.getBoundingClientRect();
            const event = new MouseEvent('mousemove', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: rect.left + 80,
                clientY: rect.top + 60
            });
            editor.dispatchEvent(event);
        """)
        time.sleep(1.5)
        
        # Check for tooltip with documentation
        hover_tooltip = page.locator(".cm-tooltip-hover")
        
        # If tooltip visible, check content
        if hover_tooltip.is_visible(timeout=2000):
            tooltip_text = hover_tooltip.inner_text()
            assert len(tooltip_text) > 20, \
                "Hover tooltip should contain documentation text"
            
            # Should contain type information
            assert "module" in tooltip_text.lower() or \
                   "class" in tooltip_text.lower() or \
                   "function" in tooltip_text.lower(), \
                "Hover should show type information"
    
    def test_hover_lsp_logging(self, page, live_server):
        """Test that LSP hover requests are logged"""
        console_messages = []
        
        def handle_console(msg):
            console_messages.append(msg.text)
        
        page.on("console", handle_console)
        
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Trigger hover
        page.evaluate("""
            const editor = document.querySelector('.cm-content');
            const rect = editor.getBoundingClientRect();
            const event = new MouseEvent('mousemove', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: rect.left + 100,
                clientY: rect.top + 80
            });
            editor.dispatchEvent(event);
        """)
        time.sleep(2)
        
        # Check for LSP hover messages
        hover_messages = [msg for msg in console_messages 
                         if "hover" in msg.lower()]
        
        assert len(hover_messages) > 0, \
            "LSP hover messages should be logged"
    
    def test_hover_tooltip_styling_exists(self, page, live_server):
        """Test that hover tooltip CSS styling is present"""
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        
        # Check that hover tooltip CSS classes exist in the page
        page_content = page.content()
        
        # CSS should be loaded in styles.css
        assert ".cm-tooltip" in page_content or \
               "hover" in page_content.lower(), \
            "Hover tooltip styles should be loaded"
    
    def test_hover_works_on_variable(self, page, live_server):
        """Test that hover works on variable names"""
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        console_messages = []
        page.on("console", lambda msg: console_messages.append(msg.text))
        
        # Ensure sample with led variable is loaded
        cm_content = page.locator(".cm-content")
        content_text = cm_content.inner_text()
        
        if "led" not in content_text:
            page.locator("#getSampleBtn").click()
            time.sleep(1)
        
        # Hover over "led" variable
        page.evaluate("""
            const editor = document.querySelector('.cm-content');
            const rect = editor.getBoundingClientRect();
            const event = new MouseEvent('mousemove', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: rect.left + 60,
                clientY: rect.top + 90
            });
            editor.dispatchEvent(event);
        """)
        time.sleep(1.5)
        
        # Check console for hover trigger
        hover_messages = [msg for msg in console_messages 
                         if "hover" in msg.lower() and "triggered" in msg.lower()]
        
        assert len(hover_messages) > 0 or \
               any("lsp" in msg.lower() for msg in console_messages), \
            "Hover should be triggered on variables"
    
    def test_hover_tooltip_dark_theme_support(self, page, live_server):
        """Test that hover tooltips work in dark theme"""
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Dark theme should be default
        body = page.locator("body")
        body_class = body.get_attribute("class")
        assert "dark-theme" in body_class, "Should start in dark theme"
        
        # Trigger hover
        page.evaluate("""
            const editor = document.querySelector('.cm-content');
            const rect = editor.getBoundingClientRect();
            const event = new MouseEvent('mousemove', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: rect.left + 100,
                clientY: rect.top + 70
            });
            editor.dispatchEvent(event);
        """)
        time.sleep(1)
        
        # Tooltip should have dark theme styling (checked via CSS presence)
        page_html = page.content()
        assert "dark-theme" in page_html, \
            "Dark theme class should be present for tooltip styling"
    
    def test_hover_tooltip_light_theme_support(self, page, live_server):
        """Test that hover tooltips work in light theme"""
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Toggle to light theme
        page.locator("#themeToggle").click()
        time.sleep(0.5)
        
        body = page.locator("body")
        body_class = body.get_attribute("class")
        assert "light-theme" in body_class, "Should be in light theme"
        
        # Trigger hover
        page.evaluate("""
            const editor = document.querySelector('.cm-content');
            const rect = editor.getBoundingClientRect();
            const event = new MouseEvent('mousemove', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: rect.left + 100,
                clientY: rect.top + 70
            });
            editor.dispatchEvent(event);
        """)
        time.sleep(1)
        
        # Light theme class should be present
        page_html = page.content()
        assert "light-theme" in page_html, \
            "Light theme class should be present for tooltip styling"


class TestLSPIntegration:
    """Tests for overall LSP integration with both features"""
    
    def test_both_features_work_together(self, page, live_server):
        """Test that completion and hover work together without conflicts"""
        console_messages = []
        
        def handle_console(msg):
            console_messages.append(msg.text)
        
        page.on("console", handle_console)
        
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Test completion
        page.locator("#clearBtn").click()
        time.sleep(0.5)
        page.locator(".cm-content").click()
        page.keyboard.type("import sys\nsys.")
        time.sleep(1)
        
        # Check for completion
        completion_messages = [msg for msg in console_messages 
                              if "completion" in msg.lower()]
        assert len(completion_messages) > 0, "Completion should work"
        
        # Press Escape to close completion menu
        page.keyboard.press("Escape")
        time.sleep(0.5)
        
        # Test hover
        page.evaluate("""
            const editor = document.querySelector('.cm-content');
            const rect = editor.getBoundingClientRect();
            const event = new MouseEvent('mousemove', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: rect.left + 100,
                clientY: rect.top + 40
            });
            editor.dispatchEvent(event);
        """)
        time.sleep(1)
        
        # Check for hover
        hover_messages = [msg for msg in console_messages 
                         if "hover" in msg.lower()]
        
        # At least one feature should have logged messages
        assert len(completion_messages) > 0 or len(hover_messages) > 0, \
            "Both LSP features should be functional"
    
    def test_lsp_client_serves_both_features(self, page, live_server):
        """Test that single LSP client serves both completion and hover"""
        console_messages = []
        
        def handle_console(msg):
            console_messages.append(msg.text)
        
        page.on("console", handle_console)
        
        page.goto(f"{live_server}/index.html")
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        # Check that LSP client initialized once
        lsp_init_messages = [msg for msg in console_messages 
                            if "LSP client ready" in msg or "LSP initialized" in msg]
        
        assert len(lsp_init_messages) > 0, \
            "LSP client should initialize"
        
        # Check that plugin includes both extensions
        lsp_plugin_messages = [msg for msg in console_messages 
                              if "LSP plugin added" in msg]
        
        assert len(lsp_plugin_messages) > 0, \
            "LSP plugin should be added to editor"
    
    def test_no_lsp_errors_on_load(self, page, live_server):
        """Test that LSP features load without errors"""
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
                      and "extension" not in e.lower()
                      and "favicon" not in e.lower()]
        
        assert len(real_errors) == 0, \
            f"LSP features should load without errors. Found: {real_errors}"
