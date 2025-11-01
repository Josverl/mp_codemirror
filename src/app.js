/**
 * CodeMirror 6 Python Editor
 * A simple Python code editor with syntax highlighting and basic features
 */

import { EditorView, basicSetup } from 'codemirror';

// Sample Python code
const sampleCode = `# MicroPython Example - Blink LED
from machine import Pin
from time import sleep

# Setup LED on GPIO2 (built-in LED on ESP32)
led = Pin(2, Pin.OUT)

def blink(times=10, delay=0.5):
    """Blink the LED a specified number of times."""
    for i in range(times):
        led.on()
        sleep(delay)
        led.off()
        sleep(delay)
    print(f"Blinked {times} times!")

# Main loop
if __name__ == "__main__":
    print("Starting blink sequence...")
    blink()
    print("Done!")
`;

// Theme configuration
let isDarkTheme = true;

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

// Initialize the editor with just basic setup (no python for now)
let view = new EditorView({
    doc: sampleCode,
    extensions: [
        basicSetup
    ],
    parent: document.getElementById('editor-container')
});

// Theme toggle functionality
function toggleTheme() {
    isDarkTheme = !isDarkTheme;
    document.body.classList.toggle('light-theme', !isDarkTheme);
    document.body.classList.toggle('dark-theme', isDarkTheme);
    
    // For now, theme changes via CSS only
    // TODO: Implement proper editor theme reconfiguration when we can use python extension
}

// Clear editor content
function clearEditor() {
    const transaction = view.state.update({
        changes: { from: 0, to: view.state.doc.length, insert: "" }
    });
    view.dispatch(transaction);
    view.focus();
}

// Load sample code
function loadSample() {
    const transaction = view.state.update({
        changes: { from: 0, to: view.state.doc.length, insert: sampleCode }
    });
    view.dispatch(transaction);
    view.focus();
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
document.getElementById('clearBtn').addEventListener('click', clearEditor);
document.getElementById('getSampleBtn').addEventListener('click', loadSample);

// Initialize with dark theme
document.body.classList.add('dark-theme');

// Export the view for testing purposes
export { view };

console.log('CodeMirror Python Editor initialized successfully!');
