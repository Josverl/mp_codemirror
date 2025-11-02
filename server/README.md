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
npm start -- --port 9011 --bot-root d:\mypython\mp_codemirror --jesse-root d:\mypython\mp_codemirror\src
```

**Parameters:**
- `--port` - WebSocket server port (default: 9011)
- `--bot-root` - Root directory of your project (where pyrightconfig.json will be deployed)
- `--jesse-root` - Directory containing your Python source files

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
