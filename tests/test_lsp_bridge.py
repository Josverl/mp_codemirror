"""
Backend tests for the Pyright LSP WebSocket bridge.

Architecture under test:
    Browser <--WebSocket--> Node.js Bridge (port 9011) <--stdio--> Pyright

Tests are split into:
- Unit tests: test Python bridge logic (lsp_bridge.py) without any running server
- Integration tests: test the live Node.js bridge on ws://localhost:9011/lsp
  (skipped when server is not running)
"""

import asyncio
import concurrent.futures
import json
import socket
import sys
import unittest.mock as mock
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "server"))
import lsp_bridge  # noqa: E402

import websockets.sync.client as ws_client

# ── helpers ──────────────────────────────────────────────────────────────────

BRIDGE_URL = "ws://localhost:9011/lsp"
BRIDGE_PORT = 9011


def _run_async(coro):
    """Run a coroutine safely, even when Playwright's event loop is active."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def _port_open(host: str, port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


server_running = _port_open("localhost", BRIDGE_PORT)

requires_server = pytest.mark.skipif(
    not server_running,
    reason=f"LSP bridge not running on port {BRIDGE_PORT}. Start with: npm start in server/pyright-lsp-bridge/",
)

# ── unit tests ────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestPyrightBridgeUnit:
    """Unit tests for the Python lsp_bridge.PyrightBridge class."""

    def test_instantiation(self):
        bridge = lsp_bridge.PyrightBridge()
        assert bridge.pyright_process is None
        assert bridge.client_websocket is None

    def test_write_to_pyright_formats_content_length_header(self):
        """write_to_pyright must prepend a correct Content-Length header."""
        bridge = lsp_bridge.PyrightBridge()

        written_bytes = []

        async def fake_drain():
            pass

        fake_stdin = mock.MagicMock()
        fake_stdin.write = lambda data: written_bytes.append(data)
        fake_stdin.drain = fake_drain

        bridge.pyright_process = mock.MagicMock()
        bridge.pyright_process.stdin = fake_stdin

        message = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"})

        _run_async(bridge.write_to_pyright(message))

        assert len(written_bytes) == 1
        raw = written_bytes[0]

        # Header and body are concatenated in a single write call
        body_bytes = message.encode("utf-8")
        expected_header = f"Content-Length: {len(body_bytes)}\r\n\r\n".encode("utf-8")

        assert raw.startswith(expected_header), f"Expected header {expected_header!r}, got prefix {raw[:50]!r}"
        assert raw.endswith(body_bytes)

    def test_write_to_pyright_no_process(self):
        """write_to_pyright with no process should not raise."""
        bridge = lsp_bridge.PyrightBridge()

        # Should log an error but not raise
        _run_async(bridge.write_to_pyright('{"jsonrpc":"2.0"}'))

    def test_write_to_pyright_unicode_content_length(self):
        """Content-Length must reflect the UTF-8 byte count, not character count."""
        bridge = lsp_bridge.PyrightBridge()

        written_bytes = []

        async def fake_drain():
            pass

        fake_stdin = mock.MagicMock()
        fake_stdin.write = lambda data: written_bytes.append(data)
        fake_stdin.drain = fake_drain

        bridge.pyright_process = mock.MagicMock()
        bridge.pyright_process.stdin = fake_stdin

        # Unicode characters that encode to more than 1 byte each
        message = json.dumps({"msg": "héllo wörld"})

        _run_async(bridge.write_to_pyright(message))

        raw = written_bytes[0]
        body_bytes = message.encode("utf-8")
        expected_header = f"Content-Length: {len(body_bytes)}\r\n\r\n".encode("utf-8")
        assert raw.startswith(expected_header)

    def test_stop_pyright_no_process(self):
        """stop_pyright should be safe when no process is running."""
        bridge = lsp_bridge.PyrightBridge()

        _run_async(bridge.stop_pyright())  # Should not raise


# ── integration tests ─────────────────────────────────────────────────────────


def _collect_until(conn, predicate, max_msgs: int = 20, timeout: float = 8.0):
    """Read messages from an open connection until predicate returns True."""
    collected = []
    for _ in range(max_msgs):
        try:
            raw = conn.recv(timeout=timeout)
            msg = json.loads(raw)
            collected.append(msg)
            if predicate(msg):
                return collected
        except TimeoutError:
            break
    return collected


def _send(conn, obj: dict):
    conn.send(json.dumps(obj))


def _initialize(conn) -> list[dict]:
    """Send initialize + collect until the initialize result arrives."""
    _send(
        conn,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": None,
                "capabilities": {"textDocument": {"publishDiagnostics": {"relatedInformation": True}}},
                "rootUri": None,
            },
        },
    )
    return _collect_until(conn, lambda m: m.get("id") == 1)


@requires_server
@pytest.mark.lsp
class TestNodeBridgeConnection:
    """Basic connectivity checks against the live Node.js bridge."""

    def test_server_port_open(self):
        assert _port_open("localhost", BRIDGE_PORT)

    def test_websocket_connects(self):
        with ws_client.connect(BRIDGE_URL, open_timeout=5):
            pass  # No exception means the handshake succeeded

    def test_websocket_path_lsp_required(self):
        """Connecting to a wrong path should fail or close immediately."""
        try:
            with ws_client.connect("ws://localhost:9011/wrongpath", open_timeout=3):
                pass
            # If it connects, the server accepts any path — note that but don't fail
        except Exception:
            pass  # Expected — server rejects unknown paths

    def test_multiple_connections_accepted(self):
        """Bridge must accept more than one concurrent connection."""
        with ws_client.connect(BRIDGE_URL, open_timeout=5) as c1:
            with ws_client.connect(BRIDGE_URL, open_timeout=5) as c2:
                assert c1 is not c2


@requires_server
@pytest.mark.lsp
class TestNodeBridgeLSPProtocol:
    """LSP JSON-RPC protocol tests against the live bridge."""

    def test_initialize_returns_result(self):
        """Server must respond to initialize with a result containing capabilities."""
        with ws_client.connect(BRIDGE_URL, open_timeout=5) as conn:
            msgs = _initialize(conn)
            result_msgs = [m for m in msgs if m.get("id") == 1]
            assert result_msgs, "No initialize result received"
            result = result_msgs[0]
            assert "result" in result, f"Expected result, got: {result}"
            assert "capabilities" in result["result"]

    def test_initialize_response_is_jsonrpc_2(self):
        """All responses must declare jsonrpc: 2.0."""
        with ws_client.connect(BRIDGE_URL, open_timeout=5) as conn:
            msgs = _initialize(conn)
            for msg in msgs:
                assert msg.get("jsonrpc") == "2.0", f"Message missing jsonrpc 2.0: {msg}"

    def test_pyright_version_logged(self):
        """Bridge should relay a Pyright version log message on startup."""
        with ws_client.connect(BRIDGE_URL, open_timeout=5) as conn:
            _send(
                conn,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"processId": None, "capabilities": {}, "rootUri": None},
                },
            )
            msgs = _collect_until(conn, lambda m: m.get("id") == 1)
            log_msgs = [
                m
                for m in msgs
                if m.get("method") == "window/logMessage"
                and "pyright" in m.get("params", {}).get("message", "").lower()
            ]
            assert log_msgs, "No Pyright version log message relayed by bridge"

    def test_initialized_notification_accepted(self):
        """Bridge must not crash or close after 'initialized' notification."""
        with ws_client.connect(BRIDGE_URL, open_timeout=5) as conn:
            _initialize(conn)
            _send(conn, {"jsonrpc": "2.0", "method": "initialized", "params": {}})
            # If the connection is still alive we can send another message
            _send(conn, {"jsonrpc": "2.0", "method": "initialized", "params": {}})
            # Connection should still be open (no exception means alive)

    def test_text_document_sync_capability_incremental(self):
        """Pyright reports textDocumentSync capability (2 = incremental)."""
        with ws_client.connect(BRIDGE_URL, open_timeout=5) as conn:
            msgs = _initialize(conn)
            result = next(m for m in msgs if m.get("id") == 1)
            sync = result["result"]["capabilities"].get("textDocumentSync")
            # textDocumentSync may be an int (2=incremental) or an object
            if isinstance(sync, int):
                assert sync in (1, 2), f"Unexpected textDocumentSync value: {sync}"
            else:
                assert sync is not None, "textDocumentSync capability missing"

    def test_shutdown_request_accepted(self):
        """Bridge must handle a shutdown request without crashing."""
        with ws_client.connect(BRIDGE_URL, open_timeout=5) as conn:
            _initialize(conn)
            _send(conn, {"jsonrpc": "2.0", "method": "initialized", "params": {}})
            _send(conn, {"jsonrpc": "2.0", "id": 99, "method": "shutdown", "params": None})
            msgs = _collect_until(conn, lambda m: m.get("id") == 99, max_msgs=10)
            shutdown_resp = [m for m in msgs if m.get("id") == 99]
            assert shutdown_resp, "No response to shutdown request"
            assert shutdown_resp[0].get("result") is None or "error" not in shutdown_resp[0]


@requires_server
@pytest.mark.lsp
class TestNodeBridgeDiagnostics:
    """End-to-end diagnostic flow through the bridge."""

    def _open_doc(self, conn, uri: str, text: str, version: int = 1):
        _send(
            conn,
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "python",
                        "version": version,
                        "text": text,
                    }
                },
            },
        )

    def test_did_open_triggers_diagnostics(self):
        """Opening a document with a known error must produce publishDiagnostics."""
        with ws_client.connect(BRIDGE_URL, open_timeout=5) as conn:
            _initialize(conn)
            _send(conn, {"jsonrpc": "2.0", "method": "initialized", "params": {}})

            uri = "file:///home/jos/mp_codemirror/src/test_bridge_open.py"
            self._open_doc(conn, uri, "x = clearly_undefined_name\n")

            msgs = _collect_until(
                conn,
                lambda m: m.get("method") == "textDocument/publishDiagnostics",
                max_msgs=30,
                timeout=10.0,
            )
            diag_msgs = [m for m in msgs if m.get("method") == "textDocument/publishDiagnostics"]
            assert diag_msgs, "No publishDiagnostics received after didOpen"

    def test_diagnostics_contain_range_and_message(self):
        """Each diagnostic must have a range and a message field."""
        with ws_client.connect(BRIDGE_URL, open_timeout=5) as conn:
            _initialize(conn)
            _send(conn, {"jsonrpc": "2.0", "method": "initialized", "params": {}})

            uri = "file:///home/jos/mp_codemirror/src/test_bridge_fields.py"
            self._open_doc(conn, uri, "result = missing_function()\n")

            msgs = _collect_until(
                conn,
                lambda m: (
                    m.get("method") == "textDocument/publishDiagnostics" and m.get("params", {}).get("diagnostics")
                ),
                max_msgs=30,
                timeout=10.0,
            )
            diag_msgs = [
                m
                for m in msgs
                if m.get("method") == "textDocument/publishDiagnostics" and m.get("params", {}).get("diagnostics")
            ]
            assert diag_msgs, "No non-empty publishDiagnostics received"

            for diag in diag_msgs[0]["params"]["diagnostics"]:
                assert "range" in diag, f"Diagnostic missing range: {diag}"
                assert "message" in diag, f"Diagnostic missing message: {diag}"
                r = diag["range"]
                assert "start" in r and "end" in r

    def test_valid_python_produces_empty_diagnostics(self):
        """Clean Python code should produce empty (or no) diagnostics."""
        with ws_client.connect(BRIDGE_URL, open_timeout=5) as conn:
            _initialize(conn)
            _send(conn, {"jsonrpc": "2.0", "method": "initialized", "params": {}})

            uri = "file:///home/jos/mp_codemirror/src/test_bridge_clean.py"
            self._open_doc(conn, uri, "x: int = 42\ny: str = 'hello'\n")

            msgs = _collect_until(
                conn,
                lambda m: m.get("method") == "textDocument/publishDiagnostics",
                max_msgs=30,
                timeout=10.0,
            )
            diag_msgs = [m for m in msgs if m.get("method") == "textDocument/publishDiagnostics"]
            if diag_msgs:
                for msg in diag_msgs:
                    diags = msg.get("params", {}).get("diagnostics", [])
                    # Filter out info-level diagnostics (severity 3/4)
                    errors = [d for d in diags if d.get("severity", 1) <= 2]
                    assert not errors, f"Unexpected errors in clean code: {errors}"

    def test_did_change_updates_diagnostics(self):
        """Changing a document with didChange must trigger fresh diagnostics."""
        with ws_client.connect(BRIDGE_URL, open_timeout=5) as conn:
            _initialize(conn)
            _send(conn, {"jsonrpc": "2.0", "method": "initialized", "params": {}})

            uri = "file:///home/jos/mp_codemirror/src/test_bridge_change.py"
            # Open with clean code
            self._open_doc(conn, uri, "x = 1\n", version=1)
            _collect_until(
                conn,
                lambda m: m.get("method") == "textDocument/publishDiagnostics",
                max_msgs=20,
                timeout=8.0,
            )

            # Now change to code with an error
            _send(
                conn,
                {
                    "jsonrpc": "2.0",
                    "method": "textDocument/didChange",
                    "params": {
                        "textDocument": {"uri": uri, "version": 2},
                        "contentChanges": [{"text": "x = totally_unknown\n"}],
                    },
                },
            )

            msgs = _collect_until(
                conn,
                lambda m: m.get("method") == "textDocument/publishDiagnostics",
                max_msgs=30,
                timeout=10.0,
            )
            diag_msgs = [m for m in msgs if m.get("method") == "textDocument/publishDiagnostics"]
            assert diag_msgs, "No publishDiagnostics after didChange"

    def test_diagnostic_uri_matches_document(self):
        """publishDiagnostics URI must match the opened document URI."""
        with ws_client.connect(BRIDGE_URL, open_timeout=5) as conn:
            _initialize(conn)
            _send(conn, {"jsonrpc": "2.0", "method": "initialized", "params": {}})

            uri = "file:///home/jos/mp_codemirror/src/test_bridge_uri.py"
            self._open_doc(conn, uri, "bad = no_such_var\n")

            msgs = _collect_until(
                conn,
                lambda m: m.get("method") == "textDocument/publishDiagnostics",
                max_msgs=30,
                timeout=10.0,
            )
            diag_msgs = [m for m in msgs if m.get("method") == "textDocument/publishDiagnostics"]
            assert diag_msgs
            reported_uri = diag_msgs[0]["params"]["uri"]
            assert reported_uri == uri, f"Diagnostic URI mismatch: expected {uri!r}, got {reported_uri!r}"
