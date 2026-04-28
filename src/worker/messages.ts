/** Message types for main thread ↔ worker communication */

export interface UserFolder {
    [key: string]: UserFolder | string | ArrayBuffer;
}

export interface MsgServerLoaded {
    type: "serverLoaded";
}

export interface MsgInitServer {
    type: "initServer";
    /** User type stubs as nested folder structure */
    userFiles: UserFolder;
    /** Project files written into /workspace before Pyright starts */
    workspaceFiles?: Record<string, string>;
    /** Custom typeshed override (zip ArrayBuffer), or false to use bundled */
    typeshedFallback: ArrayBuffer | false | undefined;
    /** Board stubs zip (ArrayBuffer), or false to skip, or undefined to use bundled default */
    boardStubs: ArrayBuffer | false | undefined;
    /** Pyright type checking mode: off, basic, standard, strict */
    typeCheckingMode?: string;
}

export interface MsgServerInitialized {
    type: "serverInitialized";
    pyrightVersion: string;
}

export interface MsgServerError {
    type: "serverError";
    error: string;
}

export interface MsgSyncFile {
    type: "syncFile";
    /** File path relative to /workspace (e.g. "helpers.py" or "lib/utils.py") */
    path: string;
    /** File text content */
    content: string;
}

export type WorkerMessage =
    | MsgServerLoaded
    | MsgInitServer
    | MsgServerInitialized
    | MsgServerError
    | MsgSyncFile;
