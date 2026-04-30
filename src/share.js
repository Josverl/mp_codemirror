/**
 * Shareable Links Module
 *
 * Encodes editor project files + settings into compact URLs.
 *
 * New format: `project=<base64url(zip(files))>`
 * Legacy format (decode-only): `code=<base64url(deflate-raw(text))>`
 */

const PROJECT_PARAM = 'project';
const LEGACY_CODE_PARAM = 'code';
// Conservative warning threshold: many intermediaries reject URLs around 8 KiB.
// Base64url expands compressed bytes, so warn before that hard limit.
const LARGE_SHARE_WARNING_BYTES = 7 * 1024;

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

// ---- Project zip helpers (new sharing format) ----

async function encodeProjectFiles(files) {
    const { strToU8, zipSync } = await import('https://esm.sh/fflate@0.8.2');
    const zipFiles = {};
    for (const [path, content] of Object.entries(files)) {
        if (!path) continue;
        zipFiles[path] = strToU8(content ?? '');
    }
    const zipped = zipSync(zipFiles);
    warnLargeSharePayload(zipped.length);
    return arrayBufferToBase64url(zipped);
}

async function decodeProjectFiles(encoded) {
    const { unzipSync, strFromU8 } = await import('https://esm.sh/fflate@0.8.2');
    const unzipped = unzipSync(base64urlToUint8Array(encoded));
    const files = {};
    for (const [path, data] of Object.entries(unzipped)) {
        if (path.endsWith('/')) continue;
        files[path] = strFromU8(data);
    }
    return files;
}

function warnLargeSharePayload(byteLength) {
    if (byteLength < LARGE_SHARE_WARNING_BYTES) return;
    const kib = Math.round(byteLength / 1024);
    console.warn(
        `Share payload is large (${kib} KiB compressed). ` +
        'Long URLs may fail through some proxies/CDNs. Consider exporting a zip file instead.'
    );
}

async function getCompressedProjectByteLength(files) {
    const { strToU8, zipSync } = await import('https://esm.sh/fflate@0.8.2');
    const zipFiles = {};
    for (const [path, content] of Object.entries(files)) {
        if (!path) continue;
        zipFiles[path] = strToU8(content ?? '');
    }
    return zipSync(zipFiles).length;
}

function normalizeShareFiles(codeOrFiles) {
    if (typeof codeOrFiles === 'string') {
        // Backward-compatible caller shape: single text buffer.
        return { 'main.py': codeOrFiles };
    }
    if (codeOrFiles && typeof codeOrFiles === 'object') {
        return codeOrFiles;
    }
    return { 'main.py': '' };
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
 * Build a shareable URL from project files and settings.
 *
 * Accepts either a single string (encoded as `main.py`) or an object map
 * of `{ path: content }`.
 *
 * @param {string|Object<string,string>} codeOrFiles
 * @param {string} board  Board ID (e.g. "esp32")
 * @param {string} typeCheckMode  Pyright type checking mode
 * @returns {Promise<string>} Full shareable URL
 */
export async function buildShareableUrl(codeOrFiles, board, typeCheckMode) {
    const url = new URL(window.location.href);
    // Remove any existing params we manage
    url.search = '';

    if (board) url.searchParams.set('board', board);
    if (typeCheckMode) url.searchParams.set('typeCheckMode', typeCheckMode);

    const projectEncoded = await encodeProjectFiles(normalizeShareFiles(codeOrFiles));
    url.searchParams.set(PROJECT_PARAM, projectEncoded);

    return url.toString();
}

/**
 * Parse shareable parameters from the current URL.
 * @returns {{ project: string|null, code: string|null, board: string|null, typeCheckMode: string|null }}
 */
export function parseUrlParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        project: params.get(PROJECT_PARAM),
        code: params.get(LEGACY_CODE_PARAM),
        board: params.get('board'),
        typeCheckMode: params.get('typeCheckMode'),
    };
}

/**
 * Restore editor state from URL parameters if present.
 *
 * New-format links decode into `files`.
 * Legacy links decode into `code`.
 *
 * @returns {Promise<{ files: Object<string,string>|null, code: string|null, board: string|null, typeCheckMode: string|null }>}
 */
export async function restoreFromUrl() {
    const { project, code: encodedLegacy, board, typeCheckMode } = parseUrlParams();
    let files = null;
    let code = null;

    if (project) {
        try {
            files = await decodeProjectFiles(project);
        } catch (err) {
            console.warn('Failed to decode project from URL:', err);
        }
    }

    if (!files && encodedLegacy) {
        try {
            code = await decompressCode(encodedLegacy);
        } catch (err) {
            console.warn('Failed to decode legacy code from URL:', err);
        }
    }

    return { files, code, board, typeCheckMode };
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
 * @param {string|Object<string,string>} codeOrFiles
 * @param {string} board
 * @param {string} typeCheckMode
 * @returns {Promise<boolean>}
 */
export async function copyShareableLink(codeOrFiles, board, typeCheckMode) {
    const url = await buildShareableUrl(codeOrFiles, board, typeCheckMode);
    return copyToClipboard(url);
}

/**
 * Copy markdown containing a shareable link.
 * @param {string|Object<string,string>} codeOrFiles
 * @param {string} board
 * @param {string} typeCheckMode
 * @returns {Promise<boolean>}
 */
export async function copyMarkdownWithLink(codeOrFiles, board, typeCheckMode) {
    const url = await buildShareableUrl(codeOrFiles, board, typeCheckMode);
    const md = `[MicroPython-stubs Playground](${url})`;
    return copyToClipboard(md);
}

/**
 * Copy markdown containing a shareable link and the code block.
 * @param {string|Object<string,string>} codeOrFiles
 * @param {string} codeBlockText
 * @param {string} board
 * @param {string} typeCheckMode
 * @returns {Promise<boolean>}
 */
export async function copyMarkdownWithLinkAndCode(codeOrFiles, codeBlockText, board, typeCheckMode) {
    const url = await buildShareableUrl(codeOrFiles, board, typeCheckMode);
    const md = `[MicroPython-stubs Playground](${url})\n\n\`\`\`python\n${codeBlockText}\n\`\`\``;
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
 * @param {() => Promise<Object<string,string>>} [getFiles] Returns full share file map
 */
export function initShareDropdown(getCode, getBoard, getTypeCheckMode, getFiles) {
    const shareBtn = document.getElementById('shareBtn');
    const dropdown = document.getElementById('shareDropdown');
    const warningEl = document.getElementById('sharePayloadWarning');
    if (!shareBtn || !dropdown) return;

    const resolveShareFiles = async () => {
        if (typeof getFiles === 'function') {
            return getFiles();
        }
        return { 'main.py': getCode() };
    };

    const updatePayloadWarning = async () => {
        if (!warningEl) return;
        warningEl.hidden = true;
        warningEl.textContent = '';

        try {
            const files = await resolveShareFiles();
            const byteLength = await getCompressedProjectByteLength(files);
            if (byteLength < LARGE_SHARE_WARNING_BYTES) return;

            const kib = Math.round(byteLength / 1024);
            warningEl.textContent =
                `Large share payload: ${kib} KiB compressed. ` +
                'Long links can fail in some proxies/CDNs. Prefer Export for big projects.';
            warningEl.hidden = false;
        } catch (err) {
            console.warn('Failed to measure share payload size:', err);
        }
    };

    // Toggle dropdown visibility
    shareBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const opening = dropdown.hidden;
        dropdown.hidden = !dropdown.hidden;
        if (opening) {
            await updatePayloadWarning();
        }
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && e.target !== shareBtn) {
            dropdown.hidden = true;
            if (warningEl) warningEl.hidden = true;
        }
    });

    // Close dropdown on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            dropdown.hidden = true;
            if (warningEl) warningEl.hidden = true;
        }
    });

    // Wire up copy buttons
    document.getElementById('copyLink')?.addEventListener('click', async (e) => {
        const files = await resolveShareFiles();
        const ok = await copyShareableLink(files, getBoard(), getTypeCheckMode());
        if (ok) flashCopied(e.currentTarget);
    });

    document.getElementById('copyMdLink')?.addEventListener('click', async (e) => {
        const files = await resolveShareFiles();
        const ok = await copyMarkdownWithLink(files, getBoard(), getTypeCheckMode());
        if (ok) flashCopied(e.currentTarget);
    });

    document.getElementById('copyMdCode')?.addEventListener('click', async (e) => {
        const files = await resolveShareFiles();
        const ok = await copyMarkdownWithLinkAndCode(files, getCode(), getBoard(), getTypeCheckMode());
        if (ok) flashCopied(e.currentTarget);
    });
}
