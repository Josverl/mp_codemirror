/**
 * CodeMirror 6 MicroPython Editor
 * A simple Python code editor with syntax highlighting and basic features
 */

import { python } from '@codemirror/lang-python';
import { Compartment } from '@codemirror/state';
import { EditorView, basicSetup } from 'codemirror';
import { createLSPClient, createLSPPlugin } from './lsp/client.js';
import { notifyDocumentChange } from './lsp/diagnostics.js';

// Sample Python code - will be loaded from file
let sampleCode = '# Loading example...\n';

// Available example files (will be populated dynamically)
let exampleFiles = [];

// LSP client and related state
let lspClient = null;
let lspTransport = null;
const documentUri = 'file:///workspace/document.py';
let documentVersion = 1;

// Debounce timer for didChange notifications
let changeDebounceTimer = null;
const CHANGE_DEBOUNCE_MS = 300; // Wait 300ms after user stops typing

// Fetch list of example files from the examples folder
async function fetchExampleFiles() {
    try {
        // Fetch the manifest file that lists all available examples
        const manifestResponse = await fetch('./examples/examples.json');
        if (!manifestResponse.ok) {
            throw new Error('Could not load examples manifest');
        }

        const filenames = await manifestResponse.json();

        // Fetch each file to get its first comment line as description
        for (const filename of filenames) {
            try {
                const contentResponse = await fetch(`./examples/${filename}`);
                if (contentResponse.ok) {
                    const content = await contentResponse.text();
                    const firstLine = content.split('\n')[0];

                    // Extract description from first comment line
                    const description = firstLine.startsWith('#')
                        ? firstLine.substring(1).trim()
                        : filename.replace('.py', '').replace(/_/g, ' ');

                    exampleFiles.push({ name: description, file: filename });
                }
            } catch (error) {
                console.warn(`Could not load ${filename}:`, error);
            }
        }

        if (exampleFiles.length === 0) {
            console.error('No example files could be loaded');
        }
    } catch (error) {
        console.error('Error fetching example files:', error);
    }
}

// Populate the example selector dropdown
function populateExampleSelector() {
    const select = document.getElementById('sampleSelect');
    exampleFiles.forEach(example => {
        const option = document.createElement('option');
        option.value = example.file;
        option.textContent = example.name;
        select.appendChild(option);
    });

    // Set default selection to first file if available
    if (exampleFiles.length > 0) {
        select.value = exampleFiles[0].file;
    }
}

// Load sample code from file
async function loadSampleFromFile(filename = 'blink_led.py') {
    try {
        const response = await fetch(`./examples/${filename}`);
        if (response.ok) {
            sampleCode = await response.text();
        } else {
            console.error('Failed to load sample file:', response.statusText);
            sampleCode = `# Error loading ${filename}\n# Please check console for details\n`;
        }
    } catch (error) {
        console.error('Error fetching sample file:', error);
        sampleCode = `# Error loading ${filename}\n# Please check console for details\n`;
    }
}

// Theme configuration
let isDarkTheme = false;  // Default to light theme

// Dark theme
const darkTheme = EditorView.theme({
    "&": {
        backgroundColor: "#1e1e1e",
        color: "#d4d4d4",
        height: "100%"
    },
    ".cm-content": {
        caretColor: "#528bff",
        fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
        fontSize: "14px",
        lineHeight: "1.5"
    },
    ".cm-cursor, .cm-dropCursor": {
        borderLeftColor: "#528bff"
    },
    "&.cm-focused .cm-selectionBackground, ::selection": {
        backgroundColor: "#264f78"
    },
    ".cm-activeLine": {
        backgroundColor: "#2a2a2a"
    },
    ".cm-selectionMatch": {
        backgroundColor: "#3a3d41"
    },
    ".cm-gutters": {
        backgroundColor: "#1e1e1e",
        color: "#858585",
        border: "none"
    },
    ".cm-activeLineGutter": {
        backgroundColor: "#2a2a2a"
    },
    ".cm-foldPlaceholder": {
        backgroundColor: "#3a3d41",
        border: "none",
        color: "#d4d4d4"
    }
}, { dark: true });

// Light theme
const lightTheme = EditorView.theme({
    "&": {
        backgroundColor: "#ffffff",
        color: "#000000",
        height: "100%"
    },
    ".cm-content": {
        caretColor: "#0000ff",
        fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
        fontSize: "14px",
        lineHeight: "1.5"
    },
    ".cm-cursor, .cm-dropCursor": {
        borderLeftColor: "#0000ff"
    },
    "&.cm-focused .cm-selectionBackground, ::selection": {
        backgroundColor: "#add6ff"
    },
    ".cm-activeLine": {
        backgroundColor: "#f0f0f0"
    },
    ".cm-selectionMatch": {
        backgroundColor: "#e8e8e8"
    },
    ".cm-gutters": {
        backgroundColor: "#f5f5f5",
        color: "#237893",
        border: "none"
    },
    ".cm-activeLineGutter": {
        backgroundColor: "#e8e8e8"
    },
    ".cm-foldPlaceholder": {
        backgroundColor: "#e8e8e8",
        border: "none",
        color: "#000000"
    }
}, { dark: false });

// Initialize the editor with basic setup and Python language support
let view;

// Initialize editor after loading sample
async function initializeEditor() {
    // Fetch available examples first
    await fetchExampleFiles();

    // Load the first available example, or use default
    const defaultFile = exampleFiles.length > 0 ? exampleFiles[0].file : 'blink_led.py';
    await loadSampleFromFile(defaultFile);

    // Initialize LSP client with WebSocket transport
    try {
        console.log('Initializing LSP client with WebSocket transport...');
        const lspResult = await createLSPClient({
            wsUrl: 'ws://localhost:9011/lsp'  // Connect to pyright LSP WS bridge server
        });
        lspClient = lspResult.client;
        lspTransport = lspResult.transport;
        console.log('LSP client ready! Connected to Pyright via WebSocket.');
    } catch (error) {
        console.error('Failed to initialize LSP client:', error);
        console.log('Editor will continue without LSP features');
        console.log('Make sure the WebSocket bridge server is running: npm start in server/python-language-server');
    }

    // Create update listener for real-time diagnostics
    const createUpdateListener = () => EditorView.updateListener.of((update) => {
        // Only send notifications if document content changed
        if (update.docChanged && lspClient) {
            // Clear existing debounce timer
            if (changeDebounceTimer) {
                clearTimeout(changeDebounceTimer);
            }

            // Debounce the change notification to avoid overwhelming the LSP server
            changeDebounceTimer = setTimeout(() => {
                const content = update.state.doc.toString();
                documentVersion++;
                
                console.log(`Sending didChange notification (version ${documentVersion})`);
                notifyDocumentChange(lspClient, documentUri, content, documentVersion);
            }, CHANGE_DEBOUNCE_MS);
        }
    });

    // Build editor extensions
    const lspCompartment = new Compartment();
    const extensions = [
        basicSetup,
        python(),
        createUpdateListener(),  // Add real-time diagnostics listener
        lspCompartment.of([])    // Start with empty LSP extensions
    ];

    // Create the editor view first
    view = new EditorView({
        doc: sampleCode,
        extensions,
        parent: document.getElementById('editor-container')
    });

    // Add LSP plugin if client is available
    if (lspClient) {
        try {
            const lspExtensions = createLSPPlugin(lspClient, view, documentUri, 'python', sampleCode);
            // Reconfigure the LSP compartment with actual extensions
            view.dispatch({
                effects: lspCompartment.reconfigure(lspExtensions)
            });
            console.log('LSP plugin added to editor');
        } catch (error) {
            console.error('Failed to add LSP plugin:', error);
        }
    }

    // Populate the example selector after editor is initialized
    populateExampleSelector();

    console.log('CodeMirror Python Editor initialized successfully!');
}

// Start initialization
initializeEditor();

// Theme toggle functionality
function toggleTheme() {
    isDarkTheme = !isDarkTheme;
    document.body.classList.toggle('light-theme', !isDarkTheme);
    document.body.classList.toggle('dark-theme', isDarkTheme);

    // Note: Currently theme changes via CSS only
    // TODO: Implement proper editor theme reconfiguration with darkTheme/lightTheme extensions
}

// Clear editor content
function clearEditor() {
    const transaction = view.state.update({
        changes: { from: 0, to: view.state.doc.length, insert: "" }
    });
    view.dispatch(transaction);
    view.focus();
}

// Trigger type checking with Pyright
function triggerTypeCheck() {
    if (!lspClient || !lspClient.connected) {
        console.warn('LSP client not connected. Cannot run type check.');
        alert('LSP client not connected. Make sure the Pyright server is running.');
        return;
    }

    try {
        const content = view.state.doc.toString();
        documentVersion++;

        console.log('Triggering type check...');
        notifyDocumentChange(lspClient, documentUri, content, documentVersion);
        console.log('Type check notification sent');

        // Visual feedback
        const button = document.getElementById('typeCheckBtn');
        const originalText = button.textContent;
        button.textContent = '⏳ Checking...';
        button.disabled = true;

        // Re-enable button after a short delay
        setTimeout(() => {
            button.textContent = originalText;
            button.disabled = false;
        }, 200);
    } catch (error) {
        console.error('Error triggering type check:', error);
        alert('Failed to run type check. Check console for details.');
    }
}

// Load sample code from selected file
async function loadSample() {
    const select = document.getElementById('sampleSelect');
    const filename = select.value;

    if (!filename) {
        alert('Please select an example file first');
        return;
    }

    await loadSampleFromFile(filename);
    const transaction = view.state.update({
        changes: { from: 0, to: view.state.doc.length, insert: sampleCode }
    });
    view.dispatch(transaction);
    view.focus();

    // Automatically trigger type check after loading a new example
    setTimeout(() => {
        triggerTypeCheck();
    }, 300); // Small delay to ensure editor update is complete
}

// Get editor content (useful for future integrations)
export function getEditorContent() {
    return view.state.doc.toString();
}

// Set editor content (useful for future integrations)
export function setEditorContent(content) {
    const transaction = view.state.update({
        changes: { from: 0, to: view.state.doc.length, insert: content }
    });
    view.dispatch(transaction);
}

// Event listeners
document.getElementById('themeToggle').addEventListener('click', toggleTheme);
document.getElementById('typeCheckBtn').addEventListener('click', triggerTypeCheck);
document.getElementById('clearBtn').addEventListener('click', clearEditor);
document.getElementById('loadSampleBtn').addEventListener('click', loadSample);

// Initialize with light theme
document.body.classList.add('light-theme');

// Export the view for testing purposes
export { view };

