# CodeMirror Editor Tests

This directory contains Playwright-based tests for the CodeMirror Python Editor.

## Running Tests

Tests use the Playwright MCP Server for exploratory testing and pytest-playwright for automated tests.

### Prerequisites

```bash
# Install playwright
pip install playwright pytest-playwright

# Install browsers
playwright install
```

### Run Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_editor.py

# Run with verbose output
pytest tests/ -v

# Run with browser visible (headed mode)
pytest tests/ --headed
```

## Test Files

- `test_editor.py` - Main editor functionality tests
- `conftest.py` - Pytest configuration and fixtures

## Writing Tests

Example test structure:

```python
def test_feature(page, live_server):
    """Test description"""
    page.goto(f"{live_server}/index.html")
    
    # Your test code here
    assert page.locator("#editor-container").is_visible()
```

## Test Coverage

Tests cover:
- Editor initialization
- Python syntax highlighting
- Theme switching
- Button functionality
- Text editing operations
- Keyboard shortcuts
- Mobile responsiveness
