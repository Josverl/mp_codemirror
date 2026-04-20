/**
 * Pyright Web Worker — runs Pyright LSP server entirely in browser.
 * 
 * Protocol:
 * 1. Worker loads → posts { type: "serverLoaded" }
 * 2. Main thread sends { type: "initServer", userFiles, typeshedFallback }
 * 3. Worker initializes ZenFS + Pyright → posts { type: "serverInitialized" }
 * 4. LSP messages flow through BrowserMessageReader/Writer
 */

// Polyfills must be imported first, in order
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

import {
    BrowserMessageReader,
    BrowserMessageWriter,
} from "vscode-languageserver/browser";
import { createConnection } from "vscode-languageserver/node";

import { PyrightServer } from "pyright/packages/pyright-internal/src/server";

import type { MsgInitServer, UserFolder, WorkerMessage } from "./messages";

// Bundled typeshed (loaded as asset URL — we'll fetch it)
// For the spike, we'll load it dynamically

const ctx = self as unknown as DedicatedWorkerGlobalScope;

/**
 * Initialize ZenFS virtual filesystem
 */
async function initFs(typeshedData?: ArrayBuffer | false) {
    const mounts: Record<string, any> = {
        "/tmp": { backend: InMemory, name: "tmp" },
        "/workspace": { backend: InMemory, name: "workspace" },
        "/typings": { backend: InMemory, name: "typings" },
    };

    if (typeshedData && typeshedData instanceof ArrayBuffer) {
        mounts["/typeshed-fallback"] = {
            backend: Zip,
            data: typeshedData,
        };
    } else {
        mounts["/typeshed-fallback"] = { backend: InMemory, name: "typeshed" };
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

/**
 * Create pyrightconfig.json in the virtual workspace
 */
function writePyrightConfig() {
    const config = {
        typeshedPath: "/typeshed-fallback",
        stubPath: "/typings",
        include: ["/workspace"],
        pythonPlatform: "Linux",
        typeCheckingMode: "standard",
        reportMissingModuleSource: "none",
        reportMissingTypeStubs: false,
    };

    fs.writeFileSync(
        "/workspace/pyrightconfig.json",
        JSON.stringify(config, null, 2)
    );
}

/**
 * Handle initialization message from main thread
 */
async function handleInitServer(msg: MsgInitServer) {
    try {
        console.log("[pyright-worker] Initializing filesystem...");
        await initFs(msg.typeshedFallback);

        // Write user type stubs
        if (msg.userFiles && Object.keys(msg.userFiles).length > 0) {
            createUserFiles("/typings", msg.userFiles);
        }

        // Write pyrightconfig
        writePyrightConfig();

        console.log("[pyright-worker] Creating Pyright server...");

        // Set up LSP connection over postMessage
        const reader = new BrowserMessageReader(ctx);
        const writer = new BrowserMessageWriter(ctx);

        // Note: createConnection from vscode-languageserver/node is used
        // because PyrightServer expects a Node-style connection.
        // The BrowserMessageReader/Writer bridge the gap.
        const connection = createConnection(reader, writer);

        // Create PyrightServer — this is the core Pyright engine
        const server = new PyrightServer(connection as any, 0);

        console.log("[pyright-worker] Pyright server created, signaling ready");
        ctx.postMessage({ type: "serverInitialized" } as WorkerMessage);
    } catch (err: any) {
        console.error("[pyright-worker] Init failed:", err);
        ctx.postMessage({
            type: "serverError",
            error: err?.message || String(err),
        } as WorkerMessage);
    }
}

// --- Worker entry point ---

ctx.onmessage = (event: MessageEvent) => {
    const msg = event.data as WorkerMessage;

    switch (msg.type) {
        case "initServer":
            handleInitServer(msg as MsgInitServer);
            break;
        default:
            // LSP messages are handled by BrowserMessageReader automatically
            break;
    }
};

// Signal that the worker script has loaded
console.log("[pyright-worker] Worker loaded, signaling ready");
ctx.postMessage({ type: "serverLoaded" } as WorkerMessage);
