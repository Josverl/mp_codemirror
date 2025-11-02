# Server Directory

This directory contains the LSP bridge servers for the CodeMirror Python editor.

## jesse-ai Pyright LSP Bridge (Recommended) ✅

**Location**: `server/pyright-lsp-bridge/` (Git Submodule)

The jesse-ai/python-language-server is added as a git submodule for easy version management and updates.

### Setup

```powershell
# Initialize submodule (if not already done)
git submodule update --init --recursive

# Install dependencies
cd server/pyright-lsp-bridge
npm install
```

### Run

```powershell
cd server/pyright-lsp-bridge
npm start -- --port 9011 --project-root d:\mypython\mp_codemirror --jesse-relative-path src --bot-relative-path tests
```

### Update Submodule

```powershell
# Update to latest version
cd server/pyright-lsp-bridge
git pull origin main

# Or from project root
git submodule update --remote server/pyright-lsp-bridge
```

## Python LSP Bridge (Legacy)

**Location**: `server/lsp_bridge.py`

Our original Python asyncio WebSocket bridge. Kept as reference and working backup.

### Setup

```powershell
# Requires Python venv with websockets
uv pip install websockets
```

### Run

```powershell
.venv\Scripts\python.exe server/lsp_bridge.py
```

**Note**: Uses port 8765 (different from jesse-ai's 9011)

## Cleanup

You can safely delete:
- `server/jesse-lsp/` - Broken prebuilt Windows package
- `server/python-language-server/` - Old clone (replaced by submodule)
