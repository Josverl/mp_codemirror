"""
Tests for the Worker Transport Layer (Phase 3).
Verifies that the WorkerTransport correctly wraps the Pyright Web Worker
and provides the same interface as WebSocketTransport.
"""
import socket
import subprocess
import time
from pathlib import Path

import pytest


def _is_port_open(host: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        return sock.connect_ex((host, port)) == 0
    except Exception:
        return False
    finally:
        sock.close()


@pytest.fixture(scope="module")
def transport_server():
    """Start HTTP server on port 8890 from project root."""
    project_root = Path(__file__).parent.parent
    port = 8890

    if _is_port_open("localhost", port):
        yield f"http://localhost:{port}"
        return

    process = subprocess.Popen(
        ["python3", "-m", "http.server", str(port)],
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for _ in range(30):
        if _is_port_open("localhost", port):
            break
        time.sleep(0.2)
    else:
        process.terminate()
        pytest.fail(f"HTTP server failed to start on port {port}")

    yield f"http://localhost:{port}"
    process.terminate()
    process.wait(timeout=5)


@pytest.fixture(scope="module")
def test_page_url(transport_server):
    return f"{transport_server}/src/tests/worker-transport-test.html"


@pytest.fixture(autouse=True)
def _set_page_timeout(page):
    """Worker tests need longer timeouts for init + diagnostics."""
    page.set_default_timeout(45000)


def test_worker_transport_connects(page, test_page_url):
    """WorkerTransport.connect() completes the handshake and resolves."""
    page.goto(test_page_url, wait_until="domcontentloaded")

    result = page.evaluate("""() => {
        return window.runTest('connect');
    }""")

    assert result["success"] is True
    assert result["connected"] is True


def test_worker_transport_lsp_initialize(page, test_page_url):
    """Full LSP initialize handshake through WorkerTransport."""
    page.goto(test_page_url, wait_until="domcontentloaded")

    result = page.evaluate("""() => {
        return window.runTest('lsp-init');
    }""")

    assert result["success"] is True
    assert len(result["capabilities"]) > 0


def test_worker_transport_diagnostics(page, test_page_url):
    """Diagnostics flow through WorkerTransport as JSON strings."""
    page.goto(test_page_url, wait_until="domcontentloaded")

    result = page.evaluate("""() => {
        return window.runTest('diagnostics');
    }""")

    assert result["success"] is True
    assert result["diagnosticCount"] >= 1
    assert len(result["message"]) > 0


def test_worker_transport_close(page, test_page_url):
    """close() terminates the worker and resets state."""
    page.goto(test_page_url, wait_until="domcontentloaded")

    result = page.evaluate("""() => {
        return window.runTest('close');
    }""")

    assert result["success"] is True
    assert result["connectedAfterClose"] is False


def test_worker_transport_messages_are_strings(page, test_page_url):
    """Subscribers receive JSON strings (not objects) matching WebSocket interface."""
    page.goto(test_page_url, wait_until="domcontentloaded")

    result = page.evaluate("""() => {
        return window.runTest('string-messages');
    }""")

    assert result["success"] is True
    assert result["allStrings"] is True
    assert result["messageCount"] > 0


def test_simple_client_with_worker_transport(page, test_page_url):
    """SimpleLSPClient works unchanged with WorkerTransport."""
    page.goto(test_page_url, wait_until="domcontentloaded")

    result = page.evaluate("""() => {
        return window.runTest('simple-client');
    }""")

    assert result["success"] is True
    assert result["hasCapabilities"] is True
    assert result["diagnosticCount"] >= 1
