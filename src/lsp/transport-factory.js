/**
 * Transport Factory for LSP Client
 *
 * Creates the appropriate transport based on mode selection.
 * Default is 'worker' (browser-based Pyright). Use 'websocket' for legacy dev bridge.
 */

import { WorkerTransport } from './worker-transport.js';
import { WebSocketTransport } from './websocket-transport.js';

/**
 * Create an LSP transport.
 * @param {Object} options
 * @param {'worker'|'websocket'} options.mode - Transport mode (default: 'worker')
 * @param {string} [options.wsUrl] - WebSocket URL (only for mode='websocket')
 * @param {string} [options.workerUrl] - Worker script URL (only for mode='worker')
 * @returns {WorkerTransport|WebSocketTransport}
 */
export function createTransport(options = {}) {
    const mode = options.mode || 'worker';

    if (mode === 'websocket') {
        const url = options.wsUrl || 'ws://localhost:9011/lsp';
        console.log(`Creating WebSocket transport → ${url}`);
        return new WebSocketTransport(url);
    }

    if (mode === 'worker') {
        const url = options.workerUrl || './worker.js';
        console.log(`Creating Worker transport → ${url}`);
        return new WorkerTransport(url, { boardStubs: options.boardStubs });
    }

    throw new Error(`Unknown transport mode: "${mode}". Use 'worker' or 'websocket'.`);
}
