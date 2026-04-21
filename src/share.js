/**
 * Shareable Links Module
 *
 * Encodes editor code + settings into compact URLs using
 * deflate-raw compression and base64url encoding.
 */

// ---- Compression helpers (native CompressionStream API) ----

/**
 * Compress a string to base64url using deflate-raw.
 * @param {string} text
 * @returns {Promise<string>} base64url-encoded compressed data
 */
export async function compressCode(text) {
    const bytes = new TextEncoder().encode(text);
    const stream = new Blob([bytes]).stream().pipeThrough(new CompressionStream('deflate-raw'));
    const compressed = await new Response(stream).arrayBuffer();
    return arrayBufferToBase64url(new Uint8Array(compressed));
}

/**
 * Decompress a base64url string back to the original text.
 * @param {string} encoded base64url-encoded compressed data
 * @returns {Promise<string>}
 */
export async function decompressCode(encoded) {
    const bytes = base64urlToUint8Array(encoded);
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
    return new Response(stream).text();
}

// ---- Base64url helpers (URL-safe, no padding) ----

function arrayBufferToBase64url(bytes) {
    let binary = '';
    for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function base64urlToUint8Array(str) {
    // Restore standard base64
    let b64 = str.replace(/-/g, '+').replace(/_/g, '/');
    // Re-pad
    while (b64.length % 4 !== 0) b64 += '=';
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
}

// ---- URL building / parsing ----

/**
 * Build a shareable URL from code and settings.
 * @param {string} code   Editor content
 * @param {string} board  Board ID (e.g. "esp32")
 * @param {string} typeCheckMode  Pyright type checking mode
 * @returns {Promise<string>} Full shareable URL
 */
export async function buildShareableUrl(code, board, typeCheckMode) {
    const url = new URL(window.location.href);
    // Remove any existing params we manage
    url.search = '';

    if (board) url.searchParams.set('board', board);
    if (typeCheckMode) url.searchParams.set('typeCheckMode', typeCheckMode);

    const compressed = await compressCode(code);
    url.searchParams.set('code', compressed);

    return url.toString();
}

/**
 * Parse shareable parameters from the current URL.
 * @returns {{ code: string|null, board: string|null, typeCheckMode: string|null }}
 */
export function parseUrlParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        code: params.get('code'),
        board: params.get('board'),
        typeCheckMode: params.get('typeCheckMode'),
    };
}

/**
 * Restore editor state from URL parameters if present.
 * Returns the decoded code string (or null if no code param), along
 * with board and typeCheckMode values.
 * @returns {Promise<{ code: string|null, board: string|null, typeCheckMode: string|null }>}
 */
export async function restoreFromUrl() {
    const { code: encoded, board, typeCheckMode } = parseUrlParams();
    let code = null;
    if (encoded) {
        try {
            code = await decompressCode(encoded);
        } catch (err) {
            console.warn('Failed to decode code from URL:', err);
        }
    }
    return { code, board, typeCheckMode };
}

// ---- Clipboard copy helpers ----

/**
 * Copy text to the clipboard.
 * @param {string} text
 * @returns {Promise<boolean>} true if copy succeeded
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch {
        // Fallback for insecure contexts / older browsers
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        const ok = document.execCommand('copy');
        document.body.removeChild(ta);
        return ok;
    }
}

/**
 * Copy the shareable link to the clipboard.
 * @param {string} code
 * @param {string} board
 * @param {string} typeCheckMode
 * @returns {Promise<boolean>}
 */
export async function copyShareableLink(code, board, typeCheckMode) {
    const url = await buildShareableUrl(code, board, typeCheckMode);
    return copyToClipboard(url);
}

/**
 * Copy markdown containing a shareable link.
 * @param {string} code
 * @param {string} board
 * @param {string} typeCheckMode
 * @returns {Promise<boolean>}
 */
export async function copyMarkdownWithLink(code, board, typeCheckMode) {
    const url = await buildShareableUrl(code, board, typeCheckMode);
    const md = `[MicroPython Editor](${url})`;
    return copyToClipboard(md);
}

/**
 * Copy markdown containing a shareable link and the code block.
 * @param {string} code
 * @param {string} board
 * @param {string} typeCheckMode
 * @returns {Promise<boolean>}
 */
export async function copyMarkdownWithLinkAndCode(code, board, typeCheckMode) {
    const url = await buildShareableUrl(code, board, typeCheckMode);
    const md = `[MicroPython Editor](${url})\n\n\`\`\`python\n${code}\n\`\`\``;
    return copyToClipboard(md);
}

// ---- Share dropdown UI ----

/**
 * Show a brief "Copied!" flash next to the button that was clicked.
 * @param {HTMLElement} button
 */
function flashCopied(button) {
    const original = button.textContent;
    button.textContent = '✓ Copied!';
    button.classList.add('share-copied');
    setTimeout(() => {
        button.textContent = original;
        button.classList.remove('share-copied');
    }, 1500);
}

/**
 * Initialise the share dropdown and wire up its buttons.
 * Call once after the DOM is ready.
 * @param {() => string} getCode          Returns current editor content
 * @param {() => string} getBoard         Returns current board ID
 * @param {() => string} getTypeCheckMode Returns current typeCheckMode
 */
export function initShareDropdown(getCode, getBoard, getTypeCheckMode) {
    const shareBtn = document.getElementById('shareBtn');
    const dropdown = document.getElementById('shareDropdown');
    if (!shareBtn || !dropdown) return;

    // Toggle dropdown visibility
    shareBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.hidden = !dropdown.hidden;
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && e.target !== shareBtn) {
            dropdown.hidden = true;
        }
    });

    // Close dropdown on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') dropdown.hidden = true;
    });

    // Wire up copy buttons
    document.getElementById('copyLink')?.addEventListener('click', async (e) => {
        const ok = await copyShareableLink(getCode(), getBoard(), getTypeCheckMode());
        if (ok) flashCopied(e.currentTarget);
    });

    document.getElementById('copyMdLink')?.addEventListener('click', async (e) => {
        const ok = await copyMarkdownWithLink(getCode(), getBoard(), getTypeCheckMode());
        if (ok) flashCopied(e.currentTarget);
    });

    document.getElementById('copyMdCode')?.addEventListener('click', async (e) => {
        const ok = await copyMarkdownWithLinkAndCode(getCode(), getBoard(), getTypeCheckMode());
        if (ok) flashCopied(e.currentTarget);
    });
}
