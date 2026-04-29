"""
Pytest configuration for CodeMirror Editor tests
"""

import signal
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

# Build artifact detection
WORKER_JS = Path(__file__).parent.parent / "dist" / "pyright_worker.js"
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


def _kill_port(port: int) -> None:
    """Kill any process listening on the given TCP port."""
    try:
        result = subprocess.run(
            ["fuser", "-k", f"{port}/tcp"],
            capture_output=True,
        )
    except FileNotFoundError:
        # fuser not available; fall back to lsof
        try:
            out = subprocess.check_output(["lsof", "-ti", f"tcp:{port}"], text=True)
            for pid in out.split():
                try:
                    import os
                    os.kill(int(pid), signal.SIGTERM)
                except (ProcessLookupError, ValueError):
                    pass
        except subprocess.CalledProcessError:
            pass  # nothing listening


def _server_responds(base_url: str, timeout: float = 3.0) -> bool:
    """Return True if the server at base_url/index.html responds with HTTP 200."""
    try:
        resp = urllib.request.urlopen(f"{base_url}/index.html", timeout=timeout)
        return resp.status == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def live_server():
    """
    Always start a fresh python3 -m http.server for the test session.

    Any existing process on port 8888 is killed first to avoid stale
    CLOSE_WAIT connections that cause every test to time out.
    The server serves from the project root so both src/ and dist/ are
    accessible; the yielded base URL is http://localhost:8888/src.
    """
    if is_port_open("localhost", 8888):
        _kill_port(8888)
        # Give the OS time to release the port
        for _ in range(10):
            if not is_port_open("localhost", 8888):
                break
            time.sleep(0.3)

    project_root = Path(__file__).parent.parent
    process = subprocess.Popen(
        ["python3", "-m", "http.server", "8888"],
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    base_url = "http://localhost:8888/src"
    # Wait until the server actually responds (up to 5 s)
    for _ in range(25):
        if _server_responds(base_url):
            break
        time.sleep(0.2)
    else:
        process.terminate()
        raise RuntimeError("HTTP server on :8888 did not respond in time")

    yield base_url
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
