/**
 * Pyright Web Worker — runs Pyright LSP server entirely in browser.
 * 
 * Protocol:
 * 1. Worker loads → posts { type: "serverLoaded" }
 * 2. Main thread sends { type: "initServer", userFiles, typeshedFallback }
 * 3. Worker initializes ZenFS + Pyright → posts { type: "serverInitialized" }
 * 4. LSP messages flow through BrowserMessageReader/Writer
 */

// Injected at build time by webpack DefinePlugin
declare const __PYRIGHT_VERSION__: string;

import "./polyfills/process-patch";
import "./polyfills/fs-patch";
import "./polyfills/timeout-patch";

// Note: 'fs' is aliased to '@zenfs/core' via webpack, so importing 'fs'
// gives us ZenFS in browser context. We also get ZenFS exports through it.
import * as fs from "fs";
import { Zip } from "@zenfs/archives";
import * as path from "path";

// ZenFS configure and InMemory are available through the fs alias
const { configure, InMemory } = fs as any;

// Bundled typeshed (inlined as ArrayBuffer by arraybuffer-loader)
import typeshedFallbackZip from "../../assets/typeshed-fallback.zip";

// Bundled default board stubs (ESP32)
import defaultBoardStubsZip from "../../assets/stubs-esp32.zip";

import {
    BrowserMessageReader,
    BrowserMessageWriter,
} from "vscode-languageserver/browser";
import { createConnection } from "vscode-languageserver/node";

import { PyrightServer } from "pyright/packages/pyright-internal/src/server";

import type { MsgInitServer, MsgSyncFile, MsgDeleteFile, UserFolder, WorkerMessage } from "./messages";

const ctx = self as unknown as DedicatedWorkerGlobalScope;

/**
 * Initialize ZenFS virtual filesystem
 */
async function initFs(
    typeshedData?: ArrayBuffer | false,
    boardStubsData?: ArrayBuffer | false
) {
    // Use bundled typeshed unless explicitly overridden
    const typeshed = typeshedData === false
        ? undefined
        : (typeshedData || typeshedFallbackZip);

    // Use bundled default board stubs unless explicitly overridden
    const boardStubs = boardStubsData === false
        ? undefined
        : (boardStubsData || defaultBoardStubsZip);

    const mounts: Record<string, any> = {
        "/tmp": { backend: InMemory, name: "tmp" },
        "/workspace": { backend: InMemory, name: "workspace" },
    };

    if (typeshed && typeshed instanceof ArrayBuffer && typeshed.byteLength > 0) {
        mounts["/typeshed-fallback"] = {
            backend: Zip,
            data: typeshed,
        };
        console.log(`[pyright-worker] Mounting typeshed (${(typeshed.byteLength / 1024 / 1024).toFixed(1)}MB)`);
    } else {
        mounts["/typeshed-fallback"] = { backend: InMemory, name: "typeshed" };
        console.warn("[pyright-worker] No typeshed data — builtins will not be resolved");
    }

    if (boardStubs && boardStubs instanceof ArrayBuffer && boardStubs.byteLength > 0) {
        mounts["/typings"] = {
            backend: Zip,
            data: boardStubs,
        };
        console.log(`[pyright-worker] Mounting board stubs (${(boardStubs.byteLength / 1024).toFixed(0)}KB)`);
    } else {
        mounts["/typings"] = { backend: InMemory, name: "typings" };
        console.log("[pyright-worker] No board stubs — MicroPython modules will not resolve");
    }

    await configure({ mounts });
}

/**
 * Write user files (type stubs) into virtual filesystem
 */
function createUserFiles(parentPath: string, folder: UserFolder) {
    fs.mkdirSync(parentPath, { recursive: true });

    for (const [name, content] of Object.entries(folder)) {
        const fullPath = path.join(parentPath, name);

        if (typeof content === "string") {
            fs.writeFileSync(fullPath, content);
        } else if (content instanceof ArrayBuffer) {
            // Mount zip at this path
            const uint8 = new Uint8Array(content);
            fs.writeFileSync(fullPath, uint8 as any);
        } else {
            // Nested folder
            createUserFiles(fullPath, content);
        }
    }
}

function writeWorkspaceFiles(files: Record<string, string> = {}) {
    for (const [relativePath, content] of Object.entries(files)) {
        const fullPath = path.join('/workspace', relativePath);
        fs.mkdirSync(path.dirname(fullPath), { recursive: true });
        fs.writeFileSync(fullPath, content);
    }
}

/**
 * Create pyrightconfig.json in the virtual workspace
 */
function writePyrightConfig(typeCheckingMode: string = "standard") {
    // Pyright requires `include`/`extraPaths` in pyrightconfig.json to be
    // RELATIVE to the config file's location (here: /workspace). Absolute
    // paths are silently dropped with "Ignoring path … because it is not
    // relative", which makes Pyright report "No source files found" and
    // breaks cross-file import resolution (e.g. `from helpers import answer`).
    //
    // `libs` is added to extraPaths so files in `libs/` can be imported by
    // bare module name (e.g. `from foo import ...`). `lib/` is intentionally
    // NOT on extraPaths: it remains a regular package, so its contents are
    // imported as `from lib.foo import ...`.
    const config = {
        typeshedPath: "/typeshed-fallback",
        stubPath: "/typings",
        include: ["."],
        extraPaths: [".", "libs"],
        pythonPlatform: "Linux",
        typeCheckingMode,
        reportMissingModuleSource: "none",
        reportMissingTypeStubs: false,
    };

    const configJson = JSON.stringify(config, null, 2);
    fs.writeFileSync(
        "/workspace/pyrightconfig.json",
        configJson
    );

}

/**
 * Handle initialization message from main thread
 */
async function handleInitServer(msg: MsgInitServer) {
    try {
        console.log("[pyright-worker] Initializing filesystem...");
        await initFs(msg.typeshedFallback, msg.boardStubs);

        // Write user type stubs
        if (msg.userFiles && Object.keys(msg.userFiles).length > 0) {
            createUserFiles("/typings", msg.userFiles);
        }

        if (msg.workspaceFiles && Object.keys(msg.workspaceFiles).length > 0) {
            writeWorkspaceFiles(msg.workspaceFiles);
        }

        // Write pyrightconfig
        writePyrightConfig(msg.typeCheckingMode || "standard");

        console.log("[pyright-worker] Creating Pyright server...");

        // Set up LSP connection over postMessage
        const reader = new BrowserMessageReader(ctx);
        const writer = new BrowserMessageWriter(ctx);

        // BrowserMessageReader's constructor assigns `ctx.onmessage`, which
        // replaces our top-level handler that processes custom worker messages
        // such as `syncFile`. Re-wrap `ctx.onmessage` here so custom messages
        // are routed to the filesystem (and to the LSP transport when needed)
        // before falling through to the JSON-RPC reader.
        const lspOnMessage = ctx.onmessage;
        ctx.onmessage = (event: MessageEvent) => {
            const data = event.data as WorkerMessage | undefined;
            if (data && typeof data === "object" && "type" in data) {
                if (data.type === "syncFile") {
                    handleSyncFile(data as MsgSyncFile);
                    return;
                }
                if (data.type === "deleteFile") {
                    handleDeleteFile(data as MsgDeleteFile);
                    return;
                }
            }
            if (lspOnMessage) {
                (lspOnMessage as (ev: MessageEvent) => void).call(ctx, event);
            }
        };

        // Note: createConnection from vscode-languageserver/node is used
        // because PyrightServer expects a Node-style connection.
        // The BrowserMessageReader/Writer bridge the gap.
        const connection = createConnection(reader, writer);

        // Create PyrightServer — this is the core Pyright engine
        const server = new PyrightServer(connection as any, 0);

        console.log("[pyright-worker] Pyright server created, signaling ready");
        ctx.postMessage({ type: "serverInitialized", pyrightVersion: __PYRIGHT_VERSION__ } as WorkerMessage);
    } catch (err: any) {
        console.error("[pyright-worker] Init failed:", err);
        ctx.postMessage({
            type: "serverError",
            error: err?.message || String(err),
        } as WorkerMessage);
    }
}

function handleSyncFile(msg: MsgSyncFile) {
    try {
        const fullPath = `/workspace/${msg.path}`;
        const dir = path.dirname(fullPath);
        fs.mkdirSync(dir, { recursive: true });
        fs.writeFileSync(fullPath, msg.content);
    } catch (err: any) {
        console.warn(`[pyright-worker] syncFile failed for ${msg.path}:`, err?.message);
    }
}

function handleDeleteFile(msg: MsgDeleteFile) {
    try {
        const fullPath = `/workspace/${msg.path}`;
        if (fs.existsSync(fullPath)) {
            fs.unlinkSync(fullPath);
        }
    } catch (err: any) {
        console.warn(`[pyright-worker] deleteFile failed for ${msg.path}:`, err?.message);
    }
}

// --- Worker entry point ---

ctx.onmessage = (event: MessageEvent) => {
    const msg = event.data as WorkerMessage;

    switch (msg.type) {
        case "initServer":
            handleInitServer(msg as MsgInitServer);
            break;
        case "syncFile":
            handleSyncFile(msg as MsgSyncFile);
            break;
        case "deleteFile":
            handleDeleteFile(msg as MsgDeleteFile);
            break;
        default:
            // LSP messages will be handled by BrowserMessageReader once the
            // server is initialized (it replaces ctx.onmessage at that point).
            break;
    }
};

// Signal that the worker script has loaded
console.log("[pyright-worker] Worker loaded, signaling ready");
ctx.postMessage({ type: "serverLoaded" } as WorkerMessage);
