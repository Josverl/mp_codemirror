/**
 * WebSocket Transport for LSP Client
 * 
 * Connects to a WebSocket server that bridges to Pyright LSP server
 */

export class WebSocketTransport {
    constructor(url = 'ws://localhost:8765') {
        this.url = url;
        this.ws = null;
        this.messageHandlers = [];
        this.errorHandlers = [];
        this.connected = false;
    }

    /**
     * Connect to the WebSocket server
     */
    async connect() {
        return new Promise((resolve, reject) => {
            console.log(`WebSocketTransport: Connecting to ${this.url}...`);
            
            try {
                this.ws = new WebSocket(this.url);
                
                this.ws.onopen = () => {
                    console.log('WebSocketTransport: Connected successfully');
                    this.connected = true;
                    resolve();
                };
                
                this.ws.onerror = (error) => {
                    console.error('WebSocketTransport: Connection error:', error);
                    this.connected = false;
                    this.errorHandlers.forEach(handler => handler(error));
                    reject(error);
                };
                
                this.ws.onclose = () => {
                    console.log('WebSocketTransport: Connection closed');
                    this.connected = false;
                };
                
                this.ws.onmessage = (event) => {
                    console.log('WebSocketTransport: Received message:', event.data.substring(0, 100));
                    this.messageHandlers.forEach(handler => handler(event.data));
                };
                
            } catch (error) {
                console.error('WebSocketTransport: Failed to create WebSocket:', error);
                reject(error);
            }
        });
    }

    /**
     * Send a message to the server
     */
    send(message) {
        if (!this.connected || !this.ws) {
            console.error('WebSocketTransport: Not connected, cannot send message');
            return;
        }
        
        console.log('WebSocketTransport: Sending message:', message.substring(0, 100));
        this.ws.send(message);
    }

    /**
     * Subscribe to messages (matches SimpleLSPClient interface)
     */
    subscribe(handler) {
        this.messageHandlers.push(handler);
    }

    /**
     * Unsubscribe from messages
     */
    unsubscribe(handler) {
        const index = this.messageHandlers.indexOf(handler);
        if (index > -1) {
            this.messageHandlers.splice(index, 1);
        }
    }

    /**
     * Register a message handler (legacy interface)
     */
    onMessage(handler) {
        this.messageHandlers.push(handler);
    }

    /**
     * Register an error handler
     */
    onError(handler) {
        this.errorHandlers.push(handler);
    }

    /**
     * Close the connection
     */
    close() {
        if (this.ws) {
            console.log('WebSocketTransport: Closing connection');
            this.ws.close();
            this.ws = null;
            this.connected = false;
        }
    }

    /**
     * Check if connected
     */
    isConnected() {
        return this.connected && this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}
