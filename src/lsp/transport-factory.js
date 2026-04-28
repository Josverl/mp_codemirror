/**
 * Transport Factory for LSP Client
 *
 * Creates a WorkerTransport for the in-browser Pyright Web Worker.
 */

import { WorkerTransport } from './worker-transport.js';

/**
 * Create an LSP transport.
 * @param {Object} options
 * @param {string} [options.workerUrl] - Worker script URL (default: './pyright_worker.js')
 * @param {ArrayBuffer} [options.boardStubs] - Board-specific stubs data
 * @param {Object.<string, string>} [options.workspaceFiles] - Project files to preload into /workspace
 * @param {string} [options.typeCheckingMode] - Pyright type checking mode
 * @returns {WorkerTransport}
 */
export function createTransport(options = {}) {
    const url = options.workerUrl || './pyright_worker.js';
    console.log(`Creating Worker transport → ${url}`);
    return new WorkerTransport(url, {
        boardStubs: options.boardStubs,
        workspaceFiles: options.workspaceFiles,
        typeCheckingMode: options.typeCheckingMode,
    });
}
