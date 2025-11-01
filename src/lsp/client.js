/**
 * LSP Client Setup for CodeMirror
 * 
 * This file sets up the LSP client with the mock transport
 * and provides helper functions for integrating LSP features.
 */

import { LSPClient } from '@codemirror/lsp-client';
import { MockTransport } from './mock-transport.js';

/**
 * Create and initialize an LSP client with mock transport
 */
export async function createLSPClient() {
    // Create the transport
    const transport = new MockTransport();
    
    // Create the client
    const client = new LSPClient({
        rootUri: 'file:///workspace',
        workspace: undefined, // Use default single-file workspace
        timeout: 5000,
        
        // No HTML sanitization needed for now (or use DOMPurify in future)
        sanitizeHTML: (html) => html,
        
        // Notification handlers
        notificationHandlers: {
            'window/logMessage': (client, params) => {
                console.log(`[LSP ${params.type}]:`, params.message);
                return true;
            },
            'window/showMessage': (client, params) => {
                console.log(`[LSP Message]:`, params.message);
                return true;
            }
        }
    });

    // Connect the client to the transport
    await client.connect(transport);
    
    // Wait for initialization
    await client.initializing;
    
    console.log('LSP Client initialized:', client.serverCapabilities);
    
    return { client, transport };
}

/**
 * Create an LSP plugin extension for an editor
 */
export function createLSPPlugin(client, fileUri = 'file:///document.py', languageId = 'python') {
    return client.plugin(fileUri, languageId);
}

/**
 * Helper to check if LSP is available and initialized
 */
export function isLSPReady(client) {
    return client && client.connected && client.serverCapabilities !== null;
}
