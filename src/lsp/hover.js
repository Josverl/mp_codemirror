/**
 * LSP Hover Tooltip Implementation for CodeMirror
 * 
 * Provides hover tooltips with type information and documentation from Pyright LSP.
 * Uses CodeMirror's hoverTooltip extension to show LSP hover results.
 */

import { hoverTooltip } from '@codemirror/view';

/**
 * Convert LSP Hover result to CodeMirror tooltip content
 * 
 * @param {Object} hover - LSP Hover result
 * @returns {HTMLElement|null} Tooltip DOM element
 */
function createHoverContent(hover) {
    if (!hover || !hover.contents) {
        return null;
    }

    const container = document.createElement('div');
    container.className = 'cm-lsp-hover';

    // Handle different content formats
    // LSP Hover contents can be: string, MarkupContent, MarkedString, or array
    let content = hover.contents;

    if (typeof content === 'string') {
        // Simple string
        const pre = document.createElement('pre');
        pre.textContent = content;
        container.appendChild(pre);
    } else if (content.kind === 'markdown') {
        // MarkupContent with markdown
        const div = document.createElement('div');
        div.className = 'cm-hover-markdown';
        
        // Simple markdown rendering (basic support)
        // For full markdown, we'd need a markdown parser library
        const text = content.value;
        
        // Handle code blocks
        if (text.includes('```')) {
            const parts = text.split('```');
            parts.forEach((part, index) => {
                if (index % 2 === 0) {
                    // Regular text
                    if (part.trim()) {
                        const p = document.createElement('p');
                        p.textContent = part.trim();
                        div.appendChild(p);
                    }
                } else {
                    // Code block
                    const pre = document.createElement('pre');
                    const code = document.createElement('code');
                    // Remove language identifier from first line
                    const lines = part.split('\n');
                    const codeText = lines.slice(1).join('\n').trim();
                    code.textContent = codeText;
                    pre.appendChild(code);
                    div.appendChild(pre);
                }
            });
        } else {
            // Simple text without code blocks
            const p = document.createElement('p');
            p.textContent = text;
            div.appendChild(p);
        }
        
        container.appendChild(div);
    } else if (content.kind === 'plaintext') {
        // MarkupContent with plain text
        const pre = document.createElement('pre');
        pre.textContent = content.value;
        container.appendChild(pre);
    } else if (Array.isArray(content)) {
        // Array of MarkedString
        content.forEach(item => {
            if (typeof item === 'string') {
                const p = document.createElement('p');
                p.textContent = item;
                container.appendChild(p);
            } else if (item.language) {
                // MarkedString with language
                const pre = document.createElement('pre');
                const code = document.createElement('code');
                code.className = `language-${item.language}`;
                code.textContent = item.value;
                pre.appendChild(code);
                container.appendChild(pre);
            }
        });
    } else if (content.language) {
        // Single MarkedString with language
        const pre = document.createElement('pre');
        const code = document.createElement('code');
        code.className = `language-${content.language}`;
        code.textContent = content.value;
        pre.appendChild(code);
        container.appendChild(pre);
    }

    return container.children.length > 0 ? container : null;
}

/**
 * Create LSP hover tooltip source for CodeMirror
 * 
 * @param {SimpleLSPClient} lspClient - The LSP client instance
 * @param {string} documentUri - The document URI
 * @returns {Function} CodeMirror hover tooltip source function
 */
export function createHoverTooltip(lspClient, documentUri) {
    return hoverTooltip(async (view, pos, side) => {
        console.log('LSP hover triggered at position:', pos);

        try {
            // Get line and character position
            const line = view.state.doc.lineAt(pos);
            const lineNumber = line.number - 1; // 0-based for LSP
            const character = pos - line.from;

            console.log(`LSP hover at line ${lineNumber + 1}, char ${character}`);

            // Send LSP hover request
            const result = await lspClient.request('textDocument/hover', {
                textDocument: { uri: documentUri },
                position: { line: lineNumber, character }
            });

            console.log('LSP hover result:', result);

            if (!result || !result.contents) {
                return null;
            }

            // Create tooltip content
            const content = createHoverContent(result);
            if (!content) {
                return null;
            }

            // Determine tooltip position range
            // Use the range from LSP if provided, otherwise use word boundaries
            let from = pos;
            let to = pos;

            if (result.range) {
                // Convert LSP range to CodeMirror positions
                const startLine = view.state.doc.line(result.range.start.line + 1);
                const endLine = view.state.doc.line(result.range.end.line + 1);
                from = startLine.from + result.range.start.character;
                to = endLine.from + result.range.end.character;
            } else {
                // Find word boundaries at cursor position
                const lineText = line.text;
                const wordMatch = /[\w\.]+/.exec(lineText.slice(0, character));
                if (wordMatch) {
                    from = line.from + character - wordMatch[0].length + wordMatch.index;
                    to = line.from + character;
                }
            }

            console.log(`Hover tooltip range: ${from} - ${to}`);

            return {
                pos: from,
                end: to,
                above: true,
                create: () => ({ dom: content })
            };

        } catch (error) {
            console.error('LSP hover error:', error);
            return null;
        }
    });
}
