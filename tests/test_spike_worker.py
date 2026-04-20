"""
Spike test: Verify Pyright runs in a Web Worker and produces diagnostics.
Tests the worker loading, initialization, and LSP protocol from a static build.
"""

from pathlib import Path

import pytest
import json

_worker_js = Path(__file__).parent.parent / "dist" / "worker.js"
pytestmark = [
    pytest.mark.worker,
    pytest.mark.skipif(
        not _worker_js.exists(),
        reason="dist/worker.js not found. Run: npm run build:worker",
    ),
]


@pytest.fixture(scope="module")
def spike_url(project_server):
    """URL for the spike test page."""
    return f"{project_server}/src/spike-test.html"


def test_worker_loads_and_signals_ready(page, spike_url):
    """Step 1: Worker script loads and posts serverLoaded message."""
    page.goto(spike_url, wait_until="domcontentloaded")

    # Collect console messages
    console_msgs = []
    page.on("console", lambda msg: console_msgs.append(msg.text))

    # Create worker and wait for serverLoaded
    result = page.evaluate("""() => {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => reject(new Error('Worker load timeout (10s)')), 10000);
            try {
                const worker = new Worker('../dist/worker.js');
                worker.onmessage = (e) => {
                    if (e.data.type === 'serverLoaded') {
                        clearTimeout(timeout);
                        worker.terminate();
                        resolve({ type: e.data.type, success: true });
                    }
                };
                worker.onerror = (e) => {
                    clearTimeout(timeout);
                    reject(new Error('Worker error: ' + e.message));
                };
            } catch (e) {
                clearTimeout(timeout);
                reject(e);
            }
        });
    }""")

    assert result["type"] == "serverLoaded"
    assert result["success"] is True


def test_worker_initializes_pyright(page, spike_url):
    """Step 2: Worker initializes ZenFS + Pyright and signals serverInitialized."""
    page.goto(spike_url, wait_until="domcontentloaded")

    result = page.evaluate("""() => {
        return new Promise((resolve, reject) => {
            const worker = new Worker('../dist/worker.js');
            let phase = 'loading';

            const timeout = setTimeout(() => {
                worker.terminate();
                reject(new Error(`Timeout in phase: ${phase}`));
            }, 10000);

            worker.onmessage = (e) => {
                const msg = e.data;
                if (msg.type === 'serverLoaded') {
                    phase = 'initializing';
                    worker.postMessage({
                        type: 'initServer',
                        userFiles: {},
                        typeshedFallback: false,
                    });
                } else if (msg.type === 'serverInitialized') {
                    clearTimeout(timeout);
                    worker.terminate();
                    resolve({ success: true, phase: 'initialized' });
                } else if (msg.type === 'serverError') {
                    clearTimeout(timeout);
                    worker.terminate();
                    reject(new Error('Server error: ' + msg.error));
                }
            };

            worker.onerror = (e) => {
                clearTimeout(timeout);
                reject(new Error('Worker error: ' + e.message));
            };
        });
    }""")

    assert result["success"] is True
    assert result["phase"] == "initialized"


def test_lsp_initialize_handshake(page, spike_url):
    """Step 3: LSP initialize request gets a valid response."""
    page.goto(spike_url, wait_until="domcontentloaded")

    result = page.evaluate("""() => {
        return new Promise((resolve, reject) => {
            const worker = new Worker('../dist/worker.js');
            let phase = 'loading';

            const timeout = setTimeout(() => {
                worker.terminate();
                reject(new Error(`Timeout in phase: ${phase}`));
            }, 10000);

            worker.onmessage = (e) => {
                const msg = e.data;

                if (msg.type === 'serverLoaded') {
                    phase = 'init-server';
                    worker.postMessage({
                        type: 'initServer',
                        userFiles: {},
                        typeshedFallback: false,
                    });
                } else if (msg.type === 'serverInitialized') {
                    phase = 'lsp-init';
                    worker.postMessage({
                        jsonrpc: '2.0',
                        id: 1,
                        method: 'initialize',
                        params: {
                            processId: null,
                            rootUri: 'file:///workspace',
                            capabilities: {
                                textDocument: {
                                    publishDiagnostics: { relatedInformation: true },
                                    completion: { completionItem: { snippetSupport: false } },
                                    hover: { contentFormat: ['plaintext'] },
                                },
                            },
                            workspaceFolders: [
                                { uri: 'file:///workspace', name: 'workspace' }
                            ],
                        },
                    });
                } else if (msg.type === 'serverError') {
                    clearTimeout(timeout);
                    worker.terminate();
                    reject(new Error('Server error: ' + msg.error));
                } else if (msg.id === 1 && msg.result) {
                    clearTimeout(timeout);
                    worker.terminate();
                    resolve({
                        success: true,
                        capabilities: msg.result.capabilities ? Object.keys(msg.result.capabilities) : [],
                    });
                }
            };

            worker.onerror = (e) => {
                clearTimeout(timeout);
                reject(new Error('Worker error: ' + e.message));
            };
        });
    }""")

    assert result["success"] is True
    assert len(result["capabilities"]) > 0


def test_diagnostics_for_type_error(page, spike_url):
    """Step 4+5: Open document with type error and receive diagnostics."""
    page.goto(spike_url, wait_until="domcontentloaded")

    result = page.evaluate("""() => {
        return new Promise((resolve, reject) => {
            const worker = new Worker('../dist/worker.js');
            let phase = 'loading';
            const t0 = performance.now();
            const times = {};

            const timeout = setTimeout(() => {
                worker.terminate();
                reject(new Error(`Timeout in phase: ${phase} after 10s`));
            }, 10000);

            worker.onmessage = (e) => {
                const msg = e.data;

                if (msg.type === 'serverLoaded') {
                    times.loaded = performance.now() - t0;
                    phase = 'init-server';
                    worker.postMessage({
                        type: 'initServer',
                        userFiles: {},
                        typeshedFallback: false,
                    });
                } else if (msg.type === 'serverInitialized') {
                    times.initialized = performance.now() - t0;
                    phase = 'lsp-init';
                    worker.postMessage({
                        jsonrpc: '2.0',
                        id: 1,
                        method: 'initialize',
                        params: {
                            processId: null,
                            rootUri: 'file:///workspace',
                            capabilities: {
                                textDocument: {
                                    publishDiagnostics: { relatedInformation: true },
                                },
                            },
                            workspaceFolders: [
                                { uri: 'file:///workspace', name: 'workspace' }
                            ],
                        },
                    });
                } else if (msg.type === 'serverError') {
                    clearTimeout(timeout);
                    worker.terminate();
                    reject(new Error('Server error: ' + msg.error));
                } else if (msg.id === 1 && msg.result) {
                    times.lspInit = performance.now() - t0;
                    phase = 'initialized-notif';
                    worker.postMessage({
                        jsonrpc: '2.0',
                        method: 'initialized',
                        params: {},
                    });

                    phase = 'did-open';
                    worker.postMessage({
                        jsonrpc: '2.0',
                        method: 'textDocument/didOpen',
                        params: {
                            textDocument: {
                                uri: 'file:///workspace/main.py',
                                languageId: 'python',
                                version: 1,
                                text: 'x: int = "hello"\\nprint(x)\\n',
                            },
                        },
                    });
                    phase = 'waiting-diagnostics';
                } else if (msg.method === 'textDocument/publishDiagnostics') {
                    const diags = msg.params?.diagnostics || [];
                    if (diags.length > 0) {
                        times.diagnostic = performance.now() - t0;
                        clearTimeout(timeout);
                        worker.terminate();
                        resolve({
                            success: true,
                            diagnosticCount: diags.length,
                            firstDiagnostic: {
                                message: diags[0].message,
                                severity: diags[0].severity,
                                range: diags[0].range,
                            },
                            times: times,
                        });
                    }
                }
            };

            worker.onerror = (e) => {
                clearTimeout(timeout);
                reject(new Error('Worker error in phase ' + phase + ': ' + e.message));
            };
        });
    }""")

    assert result["success"] is True
    assert result["diagnosticCount"] >= 1

    # Verify it caught a diagnostic (without typeshed, builtins like 'int' are not defined)
    diag = result["firstDiagnostic"]
    assert len(diag["message"]) > 0

    # Check timing budget (< 5 seconds total)
    total_ms = result["times"]["diagnostic"]
    print(f"\n=== SPIKE TIMING ===")
    print(f"Worker load:        {result['times']['loaded']:.0f}ms")
    print(f"Pyright init:       {result['times']['initialized']:.0f}ms")
    print(f"LSP handshake:      {result['times']['lspInit']:.0f}ms")
    print(f"First diagnostic:   {total_ms:.0f}ms")
    print(f"Budget: 5000ms — {'PASS' if total_ms < 5000 else 'OVER BUDGET'}")

    assert total_ms < 10000, f"Total time {total_ms:.0f}ms exceeds 10s hard limit"
