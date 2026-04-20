/**
 * LSP Client Setup for CodeMirror
 *
 * Creates and initializes an LSP client with either Worker or WebSocket transport.
 */

import { EditorState } from '@codemirror/state';
import { createCompletionSource } from './completion.js';
import { createLSPDiagnostics, notifyDocumentOpen } from './diagnostics.js';
import { createHoverTooltip } from './hover.js';
import { SimpleLSPClient } from './simple-client.js';
import { createTransport } from './transport-factory.js';

/**
 * Create and initialize an LSP client
 * @param {Object} config - Configuration options
 * @param {'worker'|'websocket'} [config.mode='worker'] - Transport mode
 * @param {string} [config.wsUrl] - WebSocket URL (for mode='websocket')
 * @param {string} [config.workerUrl] - Worker script URL (for mode='worker')
 * @param {number} [config.timeout=5000] - Request timeout in ms
 */
export async function createLSPClient(config = {}) {
    const transport = createTransport({
        mode: config.mode || 'worker',
        wsUrl: config.wsUrl,
        workerUrl: config.workerUrl,
    });

    console.log(`Creating LSP client (mode: ${config.mode || 'worker'})`);

    const client = new SimpleLSPClient({
        rootUri: 'file:///workspace',
        timeout: config.timeout || 5000,
    });

    await transport.connect();
    console.log('Transport connected');

    await client.connect(transport);
    console.log('LSP Client initialized:', client.serverCapabilities);

    return { client, transport };
}

/**
 * Create an LSP plugin extension for an editor
 */
export function createLSPPlugin(client, view, fileUri = 'file:///document.py', languageId = 'python', initialContent = '') {
    // Store client reference for later use
    if (!window.lspClients) {
        window.lspClients = new Map();
    }
    window.lspClients.set(fileUri, { client, languageId });

    // Notify server that document is open
    notifyDocumentOpen(client, fileUri, languageId, initialContent, 1);

    // Create diagnostics extension with the view
    const diagnosticsExtensions = createLSPDiagnostics(client, fileUri, view);

    // Create completion source
    const completionSource = createCompletionSource(client, fileUri);

    // Provide LSP completions through the language data facet so they
    // integrate with the existing autocompletion() from basicSetup instead
    // of creating a competing second autocomplete instance.
    const completionExtension = EditorState.languageData.of(() => [{
        autocomplete: completionSource
    }]);

    // Create hover tooltip extension
    const hoverExtension = createHoverTooltip(client, fileUri);

    // Return extensions array
    return [
        ...diagnosticsExtensions,
        completionExtension,
        hoverExtension
    ];
}

/**
 * Helper to check if LSP is available and initialized
 */
export function isLSPReady(client) {
    return client && client.connected && client.serverCapabilities !== null;
}
