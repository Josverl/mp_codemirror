# Server Directory

> **Note:** This server is for dev/debug only. For normal use, Pyright runs in a Web Worker in the browser — no server needed. Only use the WebSocket bridge when debugging LSP communication with `?lsp=websocket` mode.

This directory contains the WebSocket LSP bridge for the CodeMirror Python editor (dev/debug only).

## jesse-ai Pyright LSP Bridge

**Location**: `server/pyright-lsp-bridge/` (Git Submodule)

The jesse-ai/python-language-server is added as a git submodule for easy version management and updates.

### Setup

```bash
# Initialize submodule (if not already done)
git submodule update --init --recursive

# Install dependencies
cd server/pyright-lsp-bridge
npm install
```

### Run

```bash
cd server/pyright-lsp-bridge
npm start -- --port 9011 --bot-root /path/to/mp_codemirror --jesse-root /path/to/mp_codemirror/src
```

**Parameters:**
- `--port` - WebSocket server port (default: 9011)
- `--bot-root` - Root directory of your project (where pyrightconfig.json will be deployed)
- `--jesse-root` - Directory containing your Python source files

### Update Submodule

```bash
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

```bash
# Requires Python venv with websockets
uv pip install websockets
```

### Run

```bash
python server/lsp_bridge.py
```

**Note**: Uses port 8765 (different from jesse-ai's 9011)
