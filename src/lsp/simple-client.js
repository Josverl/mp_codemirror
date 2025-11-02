/**
 * Lightweight LSP Client for CodeMirror
 * 
 * This is a custom LSP client implementation since @codemirror/lsp-client
 * is not stable. This provides the core LSP functionality
 * needed for diagnostics, completion, and hover.
 */

/**
 * Simple LSP Client that handles the protocol
 */
export class SimpleLSPClient {
    constructor(config = {}) {
        this.config = config;
        this.transport = null;
        this.messageId = 0;
        this.pendingRequests = new Map();
        this.serverCapabilities = null;
        this.connected = false;
        this.initializing = null;
        this.messageHandlers = [];
    }

    /**
     * Connect to the LSP server via a transport
     */
    async connect(transport) {
        this.transport = transport;
        this.connected = true;

        // Subscribe to messages from transport
        transport.subscribe(this.handleMessage.bind(this));

        // Initialize the connection
        this.initializing = this.initialize();
        await this.initializing;

        return this;
    }

    /**
     * Send initialize request to server
     */
    async initialize() {
        const response = await this.request('initialize', {
            processId: null,
            rootUri: this.config.rootUri || 'file:///workspace',
            capabilities: {
                textDocument: {
                    synchronization: {
                        dynamicRegistration: false,
                        willSave: false,
                        willSaveWaitUntil: false,
                        didSave: false
                    },
                    completion: {
                        dynamicRegistration: false,
                        completionItem: {
                            snippetSupport: false,
                            commitCharactersSupport: false,
                            documentationFormat: ['plaintext', 'markdown'],
                            deprecatedSupport: false,
                            preselectSupport: false
                        },
                        contextSupport: false
                    },
                    hover: {
                        dynamicRegistration: false,
                        contentFormat: ['plaintext', 'markdown']
                    },
                    diagnostic: {
                        dynamicRegistration: false
                    }
                }
            }
        });

        this.serverCapabilities = response.capabilities;

        // Send initialized notification
        this.notify('initialized', {});

        console.log('LSP initialized, capabilities:', this.serverCapabilities);
    }

    /**
     * Send a request to the server
     */
    request(method, params) {
        return new Promise((resolve, reject) => {
            const id = ++this.messageId;
            const message = {
                jsonrpc: '2.0',
                id,
                method,
                params
            };

            this.pendingRequests.set(id, { resolve, reject });

            // Set timeout
            const timeout = setTimeout(() => {
                if (this.pendingRequests.has(id)) {
                    this.pendingRequests.delete(id);
                    reject(new Error(`Request ${method} timed out`));
                }
            }, this.config.timeout || 5000);

            // Store timeout with request
            this.pendingRequests.get(id).timeout = timeout;

            this.transport.send(JSON.stringify(message));
        });
    }

    /**
     * Send a notification to the server (no response expected)
     */
    notify(method, params) {
        const message = {
            jsonrpc: '2.0',
            method,
            params
        };
        this.transport.send(JSON.stringify(message));
    }

    /**
     * Handle incoming messages from transport
     */
    handleMessage(messageStr) {
        try {
            const message = JSON.parse(messageStr);

            // Response to a request
            if (message.id !== undefined && this.pendingRequests.has(message.id)) {
                const pending = this.pendingRequests.get(message.id);
                this.pendingRequests.delete(message.id);

                if (pending.timeout) {
                    clearTimeout(pending.timeout);
                }

                if (message.error) {
                    pending.reject(new Error(message.error.message));
                } else {
                    pending.resolve(message.result);
                }
            }
            // Notification from server
            else if (message.method) {
                this.handleNotification(message.method, message.params);
            }
        } catch (error) {
            console.error('Error handling LSP message:', error);
        }
    }

    /**
     * Handle notifications from server
     */
    handleNotification(method, params) {
        console.log(`LSP notification: ${method}`, params);

        // Call registered handlers
        this.messageHandlers.forEach(handler => {
            try {
                handler(method, params);
            } catch (error) {
                console.error('Error in message handler:', error);
            }
        });

        // Built-in handlers
        if (method === 'window/logMessage') {
            const types = ['', 'ERROR', 'WARNING', 'INFO', 'LOG'];
            console.log(`[LSP ${types[params.type]}]:`, params.message);
        } else if (method === 'window/showMessage') {
            console.log('[LSP Message]:', params.message);
        }
    }

    /**
     * Register a message handler
     */
    onNotification(handler) {
        this.messageHandlers.push(handler);
    }

    /**
     * Disconnect from server
     */
    disconnect() {
        if (this.connected) {
            try {
                this.notify('shutdown', {});
                this.notify('exit', {});
            } catch (error) {
                console.error('Error during shutdown:', error);
            }
            this.connected = false;
            this.serverCapabilities = null;
        }
    }
}
