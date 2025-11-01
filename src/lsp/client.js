/**
 * LSP Client Setup for CodeMirror
 * 
 * This file sets up the LSP client with either mock or WebSocket transport
 */

import { createLSPDiagnostics, notifyDocumentOpen } from './diagnostics.js';
import { MockTransport } from './mock-transport.js';
import { SimpleLSPClient } from './simple-client.js';
import { WebSocketTransport } from './websocket-transport.js';

/**
 * Create and initialize an LSP client
 * @param {Object} config - Configuration options
 * @param {boolean} config.useMock - Use mock transport (default: false)
 * @param {string} config.wsUrl - WebSocket URL (default: ws://localhost:8765)
 */
export async function createLSPClient(config = {}) {
    const useMock = config.useMock !== undefined ? config.useMock : false;
    const wsUrl = config.wsUrl || 'ws://localhost:8765';
    
    // Create the transport
    const transport = useMock 
        ? new MockTransport() 
        : new WebSocketTransport(wsUrl);
    
    console.log(`Creating LSP client with ${useMock ? 'Mock' : 'WebSocket'} transport`);

    // Create the client
    const client = new SimpleLSPClient({
        rootUri: 'file:///workspace',
        timeout: 5000
    });

    try {
        // Connect the WebSocket transport first (if not mock)
        if (!useMock) {
            console.log('Connecting WebSocket transport...');
            await transport.connect();
            console.log('WebSocket transport connected');
        }
        
        // Connect the client to the transport
        await client.connect(transport);
        console.log('LSP Client initialized:', client.serverCapabilities);
    } catch (error) {
        console.error('Failed to connect LSP client:', error);
        // Fall back to mock if WebSocket fails
        if (!useMock) {
            console.warn('Falling back to MockTransport');
            const mockTransport = new MockTransport();
            await client.connect(mockTransport);
            return { client, transport: mockTransport };
        }
        throw error;
    }

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
