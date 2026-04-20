# mp_codemirror - CodeMirror Python Editor with LSP support

set dotenv-load := false

# project root for LSP bridge arguments
root := justfile_directory()

# default recipe: list available recipes
default:
    @just --list

# initial project setup after cloning
setup:
    git submodule update --init --recursive
    cd server/pyright-lsp-bridge && npm install
    uv sync --extra test
    uv run playwright install --with-deps chromium
    uv pip install micropython-esp32-stubs --target typings

# start the LSP bridge server (port 9011)
lsp:
    cd server/pyright-lsp-bridge && npm start -- --port 9011 --bot-root "{{root}}" --jesse-root "{{root}}/src"

# start the HTTP server (port 8888)
http:
    python -m http.server 8888

# start both servers and open the browser
serve:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Starting LSP bridge on port 9011..."
    cd "{{root}}/server/pyright-lsp-bridge" && npm start -- --port 9011 --bot-root "{{root}}" --jesse-root "{{root}}/src" &
    LSP_PID=$!
    echo "Starting HTTP server on port 8888..."
    python -m http.server 8888 &
    HTTP_PID=$!
    sleep 2
    echo "Opening browser..."
    xdg-open http://localhost:8888/src/ 2>/dev/null || open http://localhost:8888/src/ 2>/dev/null || echo "Open http://localhost:8888/src/ in your browser"
    echo "Servers running (LSP: $LSP_PID, HTTP: $HTTP_PID). Press Ctrl+C to stop."
    trap "kill $LSP_PID $HTTP_PID 2>/dev/null" EXIT INT TERM
    wait

# run tests
test *args='':
    pytest tests/ -v {{args}}
