/**
 * LSP Diagnostics Integration for CodeMirror
 * 
 * This module integrates LSP diagnostics with CodeMirror's linting system
 * to show errors, warnings, and hints from the LSP server.
 */

import { lintGutter, setDiagnostics, openLintPanel, nextDiagnostic, previousDiagnostic } from '@codemirror/lint';
import { keymap } from '@codemirror/view';
import { Prec } from '@codemirror/state';

/**
 * Lint keyboard navigation extension (F8 / Shift-F8).
 * Opens the lint panel and navigates to next/previous diagnostic.
 * Uses high precedence to override basicSetup's default lintKeymap
 * (which only navigates without opening the panel).
 */
export const lintKeymapExtension = Prec.high(keymap.of([
    {
        key: 'F8',
        run(view) {
            openLintPanel(view);
            const result = nextDiagnostic(view);
            view.focus();
            return result;
        }
    },
    {
        key: 'Shift-F8',
        run(view) {
            openLintPanel(view);
            const result = previousDiagnostic(view);
            view.focus();
            return result;
        }
    }
]));

/**
 * Update the diagnostics status bar below the editor
 */
export function updateDiagnosticsStatus(diagnostics = []) {
    const el = document.getElementById('diagnostics-status');
    if (!el) return;

    let errors = 0, warnings = 0, info = 0;
    for (const d of diagnostics) {
        if (d.severity === 'error') errors++;
        else if (d.severity === 'warning') warnings++;
        else info++;
    }

    el.innerHTML =
        `Errors: <span class="count-error">${errors}</span>` +
        ` | Warnings: <span class="count-warning">${warnings}</span>` +
        ` | Info: <span class="count-info">${info}</span>`;
}

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
                updateDiagnosticsStatus(cmDiagnostics);
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
 * Convert LSP position (line, character) to CodeMirror offset.
 * Clamps the result to [0, doc.length] so that stale diagnostics arriving
 * after the user has edited the document never produce an out-of-bounds
 * position (which would otherwise throw a RangeError inside CodeMirror).
 */
function positionToOffset(doc, position) {
    try {
        if (position.line + 1 > doc.lines) {
            // Line no longer exists — diagnostics are from a previous document version.
            console.info('positionToOffset: line out of bounds (stale diagnostics), clamping to end of document');
            return doc.length;
        }
        const line = doc.line(position.line + 1); // LSP is 0-based, CodeMirror is 1-based
        // Clamp character offset: the character may exceed the line length when
        // the document has been shortened since Pyright started its analysis.
        return Math.min(line.from + position.character, doc.length);
    } catch (error) {
        console.info('positionToOffset: could not map position (stale diagnostics), clamping to 0:', error.message);
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
