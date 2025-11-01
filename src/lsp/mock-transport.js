/**
 * Mock LSP Transport for Testing
 * 
 * This transport simulates an LSP server for testing purposes
 * without requiring a real Pyright server connection.
 */

export class MockTransport {
    constructor() {
        this.handlers = [];
        this.messageId = 0;
    }

    /**
     * Send a message to the mock server
     * Generates mock responses based on the LSP method
     */
    send(message) {
        try {
            const msg = JSON.parse(message);
            console.log('MockTransport sent:', msg);

            // Generate mock response based on message type
            if (msg.id !== undefined) {
                // This is a request - generate response
                setTimeout(() => {
                    const response = this.generateMockResponse(msg);
                    if (response) {
                        this.handlers.forEach(h => h(JSON.stringify(response)));
                    }
                }, 100); // Simulate network delay
            }

            // Handle didOpen notification - simulate diagnostics
            if (msg.method === 'textDocument/didOpen') {
                setTimeout(() => {
                    this.simulateDiagnostics(msg.params.textDocument.uri);
                }, 500);
            }

            // Notifications don't need responses
        } catch (error) {
            console.error('Error parsing message in MockTransport:', error);
        }
    }

    /**
     * Generate mock responses based on LSP method
     */
    generateMockResponse(msg) {
        const { id, method, params } = msg;

        switch (method) {
            case 'initialize':
                return {
                    jsonrpc: '2.0',
                    id,
                    result: {
                        capabilities: {
                            textDocumentSync: 1, // Full sync
                            completionProvider: {
                                resolveProvider: true,
                                triggerCharacters: ['.', '(']
                            },
                            hoverProvider: true,
                            diagnosticProvider: {
                                interFileDependencies: false,
                                workspaceDiagnostics: false
                            },
                            definitionProvider: true,
                            referencesProvider: true,
                            signatureHelpProvider: {
                                triggerCharacters: ['(', ',']
                            }
                        },
                        serverInfo: {
                            name: 'Mock Pyright Server',
                            version: '1.0.0-mock'
                        }
                    }
                };

            case 'textDocument/completion':
                return {
                    jsonrpc: '2.0',
                    id,
                    result: {
                        isIncomplete: false,
                        items: this.getMockCompletions(params)
                    }
                };

            case 'textDocument/hover':
                return {
                    jsonrpc: '2.0',
                    id,
                    result: this.getMockHover(params)
                };

            case 'textDocument/diagnostic':
                return {
                    jsonrpc: '2.0',
                    id,
                    result: {
                        kind: 'full',
                        items: this.getMockDiagnostics(params)
                    }
                };

            case 'shutdown':
                return {
                    jsonrpc: '2.0',
                    id,
                    result: null
                };

            default:
                console.log(`MockTransport: unhandled method ${method}`);
                return {
                    jsonrpc: '2.0',
                    id,
                    result: null
                };
        }
    }

    /**
     * Generate mock completion suggestions
     */
    getMockCompletions(params) {
        const completions = [
            {
                label: 'print',
                kind: 3, // Function
                detail: 'built-in function',
                documentation: 'Print objects to the text stream',
                insertText: 'print($0)',
                insertTextFormat: 2 // Snippet
            },
            {
                label: 'len',
                kind: 3, // Function
                detail: 'built-in function',
                documentation: 'Return the length of an object',
                insertText: 'len($0)',
                insertTextFormat: 2
            },
            {
                label: 'range',
                kind: 3, // Function
                detail: 'built-in function',
                documentation: 'Return an object that produces a sequence of integers',
                insertText: 'range($0)',
                insertTextFormat: 2
            },
            {
                label: 'str',
                kind: 7, // Class
                detail: 'built-in class',
                documentation: 'String class',
                insertText: 'str'
            },
            {
                label: 'int',
                kind: 7, // Class
                detail: 'built-in class',
                documentation: 'Integer class',
                insertText: 'int'
            },
            {
                label: 'list',
                kind: 7, // Class
                detail: 'built-in class',
                documentation: 'List class',
                insertText: 'list'
            },
            {
                label: 'dict',
                kind: 7, // Class
                detail: 'built-in class',
                documentation: 'Dictionary class',
                insertText: 'dict'
            }
        ];

        return completions;
    }

    /**
     * Generate mock hover information
     */
    getMockHover(params) {
        // Simple mock: return type information for common symbols
        return {
            contents: {
                kind: 'markdown',
                value: '```python\n(function) print(*values, sep=" ", end="\\n", file=None)\n```\n\nPrint objects to the text stream.'
            },
            range: {
                start: params.position,
                end: { line: params.position.line, character: params.position.character + 5 }
            }
        };
    }

    /**
     * Generate mock diagnostics
     */
    getMockDiagnostics(params) {
        // Parse the document text and look for simple errors
        // This is a very basic implementation
        const diagnostics = [];

        // In a real implementation, this would be done by analyzing the Python code
        // For now, we'll just return some example diagnostics to test the UI

        // Example: missing colon detection (very basic)
        // In reality, Pyright would do sophisticated analysis

        return diagnostics;
    }

    /**
     * Subscribe to messages from the mock server
     */
    subscribe(handler) {
        this.handlers.push(handler);
    }

    /**
     * Unsubscribe from messages
     */
    unsubscribe(handler) {
        const index = this.handlers.indexOf(handler);
        if (index > -1) {
            this.handlers.splice(index, 1);
        }
    }

    /**
     * Simulate server-initiated diagnostics
     * This would typically be called after document changes
     */
    publishDiagnostics(uri, diagnostics) {
        const notification = {
            jsonrpc: '2.0',
            method: 'textDocument/publishDiagnostics',
            params: {
                uri,
                diagnostics
            }
        };

        setTimeout(() => {
            this.handlers.forEach(h => h(JSON.stringify(notification)));
        }, 200);
    }

    /**
     * Simulate diagnostics for testing
     * This generates some mock diagnostics to demonstrate the feature
     */
    simulateDiagnostics(uri) {
        // Create a test diagnostic to demonstrate the feature
        const testDiagnostics = [
            {
                range: {
                    start: { line: 1, character: 5 },
                    end: { line: 1, character: 12 }
                },
                severity: 3, // Information
                message: 'LSP diagnostics are working! This is a test message.',
                source: 'mock-pyright'
            }
        ];

        console.log('Simulating diagnostics for:', uri);
        this.publishDiagnostics(uri, testDiagnostics);
    }
}

/**
 * Example diagnostics for testing
 */
export function createMockDiagnostic(line, character, message, severity = 1) {
    return {
        range: {
            start: { line, character },
            end: { line, character: character + 10 }
        },
        severity, // 1 = Error, 2 = Warning, 3 = Information, 4 = Hint
        message,
        source: 'mock-pyright'
    };
}
