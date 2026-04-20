"""
Pytest configuration for CodeMirror Editor tests
"""

import socket
import subprocess
import time
import urllib.request
from pathlib import Path

# Build artifact detection
WORKER_JS = Path(__file__).parent.parent / "dist" / "worker.js"
worker_available = WORKER_JS.exists()

import pytest
from playwright.sync_api import sync_playwright


def is_port_open(host: str, port: int) -> bool:
    """Check if a TCP port is accepting connections."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        return sock.connect_ex((host, port)) == 0
    except Exception:
        return False
    finally:
        sock.close()


def _detect_server_base_url() -> str | None:
    """Return the base URL of the HTTP server on :8888 by probing known paths."""
    for candidate in (
        "http://localhost:8888/index.html",
        "http://localhost:8888/src/index.html",
    ):
        try:
            resp = urllib.request.urlopen(candidate, timeout=2)
            if resp.status == 200:
                return candidate.removesuffix("/index.html")
        except Exception:
            pass
    return None


# Evaluate at collection time so skipif decorators work correctly.
_lsp_available = is_port_open("localhost", 9011)


@pytest.fixture(scope="session")
def lsp_available() -> bool:
    """Return True when the Pyright LSP bridge is reachable on port 9011."""
    return _lsp_available


@pytest.fixture(scope="session")
def lsp_server(lsp_available):
    """
    Skip (not fail) when the LSP bridge is not running.
    Start the bridge with: Run Task > 'Start LSP Bridge'
    """
    if not lsp_available:
        pytest.skip(
            "LSP bridge not running on port 9011. "
            "Start with: Run Task > 'Start LSP Bridge' or "
            "'npm start' in server/pyright-lsp-bridge/"
        )
    yield "ws://localhost:9011/lsp"


@pytest.fixture(scope="session")
def live_server():
    """
    Provide the base URL for the editor.  Reuses an already-running server on
    :8888 (detecting whether it serves from the project root or src/), and
    starts a fresh one only when the port is free.
    """
    if is_port_open("localhost", 8888):
        base = _detect_server_base_url()
        yield base or "http://localhost:8888"
        return

    # Serve from project root so both src/ and dist/ are accessible
    project_root = Path(__file__).parent.parent
    process = subprocess.Popen(
        ["python3", "-m", "http.server", "8888"],
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1)
    yield "http://localhost:8888/src"
    process.terminate()
    process.wait()


@pytest.fixture(scope="session")
def project_server(live_server):
    """Base URL serving the project root (for tests that need both src/ and dist/).

    If live_server already points to root, returns it as-is.
    If it points to /src, returns the parent.
    """
    if live_server.endswith("/src"):
        yield live_server.removesuffix("/src")
    else:
        yield live_server


@pytest.fixture(scope="session")
def browser():
    """Single browser instance shared across the test session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser):
    """Fresh page (and context) for every test function."""
    # ignore_https_errors lets CDN resources load behind TLS interception proxies
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    yield page
    page.close()
    context.close()


@pytest.fixture(scope="module")
def shared_page(browser):
    """Module-scoped page for read-only tests. Avoids CDN re-downloads."""
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    yield page
    page.close()
    context.close()
