"""
Pytest configuration for CodeMirror Editor tests
"""
import os
import subprocess
import time
from pathlib import Path

import pytest


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
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(2)
    
    # Yield the server URL
    yield "http://localhost:8888"
    
    # Cleanup: terminate the server
    process.terminate()
    process.wait()


@pytest.fixture(scope="function")
def page(playwright):
    """Create a new browser page for each test"""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    yield page
    
    # Cleanup
    context.close()
    browser.close()
