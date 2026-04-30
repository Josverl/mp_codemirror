/**
 * LSP Completion Integration for CodeMirror
 * 
 * This module integrates LSP textDocument/completion requests with CodeMirror's
 * autocomplete system, providing intelligent code completion from Pyright.
 */

import {
    computeCompletionFrom,
    convertCompletionItem,
    dedupeAndSortCompletionOptions,
} from './completion-core.mjs';

/**
 * Create LSP completion source for CodeMirror
 * 
 * @param {SimpleLSPClient} lspClient - The LSP client instance
 * @param {string} documentUri - The document URI (e.g., 'file:///workspace/document.py')
 * @returns {Function} CodeMirror completion source function
 */
export function createCompletionSource(lspClient, documentUri) {
    return async (context) => {
        console.log('LSP completion source called, explicit:', context.explicit);

        // Try to match dotted attribute access (e.g., "sys.") or just words
        let word = context.matchBefore(/[\w\.]+/);

        // Only complete when explicitly requested or when we have something to complete
        if (!word || (word.from === word.to && !context.explicit)) {
            console.log('LSP completion: Rejected - no match or not explicit');
            return null;
        }

        // Get cursor position
        const pos = context.pos;
        const line = context.state.doc.lineAt(pos);
        const lineText = line.text;
        const character = pos - line.from;
        const lineNumber = context.state.doc.lineAt(pos).number - 1; // 0-based

        console.log(`LSP completion at line ${lineNumber + 1}, char ${character}, word: "${word.text}"`);

        // Determine the starting position for completion
        // For dotted access like "sys.arg", start from after the last dot
        // so CodeMirror filters completions against "arg" not "sys.arg"
        const from = computeCompletionFrom(word);

        try {
            console.log('Sending textDocument/completion request to LSP...');

            // Send textDocument/completion request to LSP
            const result = await lspClient.request('textDocument/completion', {
                textDocument: {
                    uri: documentUri
                },
                position: {
                    line: lineNumber,
                    character: character
                },
                context: {
                    triggerKind: context.explicit ? 1 : 2, // 1=Invoked, 2=TriggerCharacter
                    triggerCharacter: lineText[character - 1] === '.' ? '.' : undefined
                }
            });

            // Handle both CompletionList and CompletionItem[] responses
            const items = result?.items || result || [];

            if (!items || items.length === 0) {
                return null;
            }

            // Convert, dedupe, and rank LSP completion options before returning.
            const options = dedupeAndSortCompletionOptions(items.map(convertCompletionItem));

            return {
                from,
                options,
                validFor: /^[\w\.]*$/
            };
        } catch (error) {
            console.error('LSP completion error:', error);
            return null;
        }
    };
}
