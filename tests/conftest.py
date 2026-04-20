"""
Pytest configuration for CodeMirror Editor tests
"""

import socket
import subprocess
import time
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright


def is_port_open(host, port):
    """Check if a port is open"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.fixture(scope="session")
def lsp_server():
    """
    Verify the Pyright LSP bridge server is running.
    Note: The server should be started manually via VSCode tasks or 'npm start' 
    before running tests.
    """
    # Check if LSP server is running on port 9011
    if not is_port_open("localhost", 9011):
        pytest.fail(
            "LSP server is not running on port 9011. "
            "Start it with: Run Task > 'Start All Servers' or 'npm start' in server/pyright-lsp-bridge"
        )
    
    yield "ws://localhost:9011/lsp"


@pytest.fixture(scope="session")
def live_server():
    """
    Start or verify HTTP server is running.
    If port 8888 is already in use, assume server is running and use it.
    Otherwise, start a new server.
    """
    server_url = "http://localhost:8888"
    
    # Check if server is already running
    if is_port_open("localhost", 8888):
        # Server already running, use it
        yield server_url
        return
    
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
    yield server_url

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
    # ignore_https_errors allows CDN resources to load in environments
    # where a TLS interception proxy is in use (e.g. CI/CD sandboxes)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    
    yield page
    
    # Cleanup
    page.close()
    context.close()
