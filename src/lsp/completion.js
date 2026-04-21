/**
 * LSP Completion Integration for CodeMirror
 * 
 * This module integrates LSP textDocument/completion requests with CodeMirror's
 * autocomplete system, providing intelligent code completion from Pyright.
 */

/**
 * LSP CompletionItemKind enum (subset we care about)
 */
const CompletionItemKind = {
    Text: 1,
    Method: 2,
    Function: 3,
    Constructor: 4,
    Field: 5,
    Variable: 6,
    Class: 7,
    Interface: 8,
    Module: 9,
    Property: 10,
    Unit: 11,
    Value: 12,
    Enum: 13,
    Keyword: 14,
    Snippet: 15,
    Color: 16,
    File: 17,
    Reference: 18,
    Folder: 19,
    EnumMember: 20,
    Constant: 21,
    Struct: 22,
    Event: 23,
    Operator: 24,
    TypeParameter: 25
};

/**
 * Convert LSP CompletionItemKind to CodeMirror completion type
 */
function kindToType(kind) {
    switch (kind) {
        case CompletionItemKind.Method:
        case CompletionItemKind.Function:
        case CompletionItemKind.Constructor:
            return 'function';
        case CompletionItemKind.Field:
        case CompletionItemKind.Property:
            return 'property';
        case CompletionItemKind.Variable:
        case CompletionItemKind.Constant:
            return 'variable';
        case CompletionItemKind.Class:
        case CompletionItemKind.Interface:
        case CompletionItemKind.Struct:
            return 'class';
        case CompletionItemKind.Module:
            return 'namespace';
        case CompletionItemKind.Keyword:
            return 'keyword';
        case CompletionItemKind.Enum:
        case CompletionItemKind.EnumMember:
            return 'enum';
        case CompletionItemKind.TypeParameter:
            return 'type';
        default:
            return 'text';
    }
}

/**
 * Convert LSP CompletionItem to CodeMirror completion option
 */
function convertCompletionItem(item) {
    return {
        label: item.label,
        type: kindToType(item.kind),
        detail: item.detail || '',
        info: item.documentation?.value || item.documentation || '',
        apply: item.insertText || item.label,
        boost: item.preselect ? 99 : undefined
    };
}

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
        const dotIndex = word.text.lastIndexOf('.');
        const from = dotIndex >= 0 ? word.from + dotIndex + 1 : word.from;

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

            // Convert LSP completion items to CodeMirror format
            const options = items.map(convertCompletionItem);

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
