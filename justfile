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
    npm install --ignore-scripts
    uv sync --extra test
    uv run playwright install --with-deps chromium
    uv pip install micropython-esp32-stubs --target typings
    just pack-typeshed

# --- Build recipes ---

# build the Pyright web worker (production)
build:
    just pack-typeshed
    just pack-stubs
    npx webpack --mode production

# build the Pyright web worker (development, with source maps)
build-dev:
    just pack-typeshed
    just pack-stubs
    npx webpack --mode development

# pack Pyright's typeshed-fallback into a zip for browser use
pack-typeshed:
    node scripts/pack-typeshed.mjs

# pack MicroPython board stubs into zip files for each board
pack-stubs:
    node scripts/pack-stubs.mjs

# rebuild everything from scratch
rebuild:
    npm install --ignore-scripts
    just pack-typeshed
    just pack-stubs
    npx webpack --mode production

# --- Server recipes ---

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

# --- Test recipes ---

# run tests
test *args='':
    pytest tests/ -v {{args}}

# run only the spike/worker tests
test-worker *args='':
    pytest tests/test_spike_worker.py -v {{args}}

# --- Info recipes ---

# show bundle sizes
sizes:
    #!/usr/bin/env bash
    echo "=== Bundle Sizes ==="
    if [ -f dist/worker.js ]; then
        SIZE=$(stat -c%s dist/worker.js 2>/dev/null || stat -f%z dist/worker.js 2>/dev/null)
        GZIP=$(gzip -c dist/worker.js | wc -c)
        printf "worker.js:          %s (%s gzipped)\n" "$(numfmt --to=iec $SIZE 2>/dev/null || echo ${SIZE}B)" "$(numfmt --to=iec $GZIP 2>/dev/null || echo ${GZIP}B)"
    else
        echo "worker.js:          not built (run 'just build')"
    fi
    if [ -f assets/typeshed-fallback.zip ]; then
        SIZE=$(stat -c%s assets/typeshed-fallback.zip 2>/dev/null || stat -f%z assets/typeshed-fallback.zip 2>/dev/null)
        printf "typeshed-fallback:  %s\n" "$(numfmt --to=iec $SIZE 2>/dev/null || echo ${SIZE}B)"
    else
        echo "typeshed-fallback:  not packed (run 'just pack-typeshed')"
    fi
