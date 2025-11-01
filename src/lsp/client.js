/**
 * LSP Client Setup for CodeMirror
 * 
 * This file sets up the LSP client with the mock transport
 * and provides helper functions for integrating LSP features.
 */

import { createLSPDiagnostics, notifyDocumentOpen } from './diagnostics.js';
import { MockTransport } from './mock-transport.js';
import { SimpleLSPClient } from './simple-client.js';

/**
 * Create and initialize an LSP client with mock transport
 */
export async function createLSPClient() {
    // Create the transport
    const transport = new MockTransport();

    // Create the client
    const client = new SimpleLSPClient({
        rootUri: 'file:///workspace',
        timeout: 5000
    });

    // Connect the client to the transport
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

    // Return extensions array
    return diagnosticsExtensions;
}

/**
 * Helper to check if LSP is available and initialized
 */
export function isLSPReady(client) {
    return client && client.connected && client.serverCapabilities !== null;
}
