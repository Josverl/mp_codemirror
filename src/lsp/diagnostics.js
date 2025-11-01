/**
 * LSP Diagnostics Integration for CodeMirror
 * 
 * This module integrates LSP diagnostics with CodeMirror's linting system
 * to show errors, warnings, and hints from the LSP server.
 */

import { lintGutter, setDiagnostics } from '@codemirror/lint';

/**
 * Create a diagnostic linter that receives diagnostics from LSP
 */
export function createLSPDiagnostics(client, fileUri, view) {
    // Listen for diagnostic notifications from the server
    client.onNotification((method, params) => {
        if (method === 'textDocument/publishDiagnostics') {
            if (params.uri === fileUri) {
                const lspDiagnostics = params.diagnostics || [];
                console.log('Received diagnostics:', lspDiagnostics);

                // Convert LSP diagnostics to CodeMirror format
                const cmDiagnostics = lspDiagnostics.map(diag => {
                    const converted = convertLSPDiagnostic(diag, view.state.doc);
                    console.log('LSP diagnostic:', diag);
                    console.log('Converted to CM diagnostic:', converted);
                    return converted;
                });

                console.log('Converted diagnostics:', cmDiagnostics);

                // Use setDiagnostics to update the editor
                view.dispatch(setDiagnostics(view.state, cmDiagnostics));
                console.log('Dispatched setDiagnostics');
            }
        }
    });

    // Return linter extension with gutter
    return [lintGutter()];
}

/**
 * Convert LSP diagnostic to CodeMirror diagnostic
 */
function convertLSPDiagnostic(lspDiag, doc) {
    // LSP uses line/character positions, CodeMirror uses absolute offsets
    const from = positionToOffset(doc, lspDiag.range.start);
    const to = positionToOffset(doc, lspDiag.range.end);

    // Map LSP severity to CodeMirror severity
    const severity = lspSeverityToString(lspDiag.severity);

    return {
        from,
        to,
        severity,
        message: lspDiag.message,
        source: lspDiag.source || 'lsp'
    };
}

/**
 * Convert LSP position (line, character) to CodeMirror offset
 */
function positionToOffset(doc, position) {
    try {
        const line = doc.line(position.line + 1); // LSP is 0-based, CodeMirror is 1-based
        return line.from + position.character;
    } catch (error) {
        console.error('Error converting position to offset:', error);
        return 0;
    }
}

/**
 * Convert LSP severity number to CodeMirror severity string
 */
function lspSeverityToString(severity) {
    // LSP: 1 = Error, 2 = Warning, 3 = Information, 4 = Hint
    // CodeMirror: 'error', 'warning', 'info'
    switch (severity) {
        case 1: return 'error';
        case 2: return 'warning';
        case 3: return 'info';
        case 4: return 'info';
        default: return 'error';
    }
}

/**
 * Request diagnostics from the server (pull diagnostics)
 */
export async function requestDiagnostics(client, fileUri, documentText) {
    try {
        // Some servers support pull diagnostics via textDocument/diagnostic
        if (client.serverCapabilities?.diagnosticProvider) {
            const result = await client.request('textDocument/diagnostic', {
                textDocument: {
                    uri: fileUri
                }
            });

            if (result && result.items) {
                return result.items;
            }
        }
    } catch (error) {
        console.error('Error requesting diagnostics:', error);
    }

    return [];
}

/**
 * Send document change notification to trigger diagnostics
 */
export function notifyDocumentChange(client, fileUri, content, version = 1) {
    client.notify('textDocument/didChange', {
        textDocument: {
            uri: fileUri,
            version
        },
        contentChanges: [{
            text: content
        }]
    });
}

/**
 * Send document open notification
 */
export function notifyDocumentOpen(client, fileUri, languageId, content, version = 1) {
    client.notify('textDocument/didOpen', {
        textDocument: {
            uri: fileUri,
            languageId,
            version,
            text: content
        }
    });
}
