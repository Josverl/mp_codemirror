"""
Pytest configuration for CodeMirror Editor tests
"""

import subprocess
import time
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def live_server():
    """Start a local HTTP server for testing"""
    # Get the src directory path
    src_dir = Path(__file__).parent.parent / "src"

    # Start the HTTP server in the background
    process = subprocess.Popen(
        ["python", "-m", "http.server", "8888"],
        cwd=str(src_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    time.sleep(1)

    # Yield the server URL
    yield "http://localhost:8888"

    # Cleanup: terminate the server
    process.terminate()
    process.wait()


@pytest.fixture(scope="session")
def browser():
    """Create a browser instance for the entire test session"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser):
    """Create a new page for each test (reusing the browser)"""
    context = browser.new_context()
    page = context.new_page()
    
    yield page
    
    # Cleanup
    page.close()
    context.close()
