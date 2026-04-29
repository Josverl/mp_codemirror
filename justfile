# mp_codemirror - CodeMirror Python Editor with LSP support

# Set shell for Windows OSs:
set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

set dotenv-load := false

# default recipe: list available recipes
default:
    @just --list

# initial project setup after cloning
setup:
    npm install --ignore-scripts
    uv sync --extra test
    uv run playwright install --with-deps chromium
    just build

# --- Build recipes ---

# build the Pyright web worker (production)
build:
    just pack
    npx webpack --mode production

# build the Pyright web worker (development, with source maps)
build-dev:
    npx webpack --mode development

# pack Pyright's typeshed-fallback into a zip for browser use
pack-typeshed:
    uv run scripts/pack-typeshed.py

# pack MicroPython board stubs into zip files for each board
pack-stubs:
    uv run scripts/pack-stubs.py

# pack MicroPython board stubs and typeshed-fallback
pack:
    just pack-typeshed
    just pack-stubs

# rebuild everything from scratch
rebuild:
    npm install --ignore-scripts
    npx webpack --mode production

# format Python code with ruff
format:
    ruff format tests/

# --- Server recipes ---

# start the threaded HTTP server (port 8888)
http:
    python tests/http_server.py 8888 .

# start the HTTP server and open the browser (Unix)
serve:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Starting HTTP server on port 8888..."
    python tests/http_server.py 8888 . &
    HTTP_PID=$!
    sleep 2
    echo "Opening browser..."
    xdg-open http://localhost:8888/src/ 2>/dev/null || open http://localhost:8888/src/ 2>/dev/null || echo "Open http://localhost:8888/src/ in your browser"
    echo "Server running (HTTP: $HTTP_PID). Press Ctrl+C to stop."
    trap "kill $HTTP_PID 2>/dev/null" EXIT INT TERM
    wait

# --- Test recipes ---

# run tests
test *args='':
    pytest tests/ -v {{args}}

# run only the worker transport tests
test-worker *args='':
    pytest tests/test_worker_transport.py -v {{args}}

# --- Info recipes ---

# show bundle sizes
sizes:
    #!/usr/bin/env bash
    echo "=== Bundle Sizes ==="
    if [ -f dist/pyright_worker.js ]; then
        SIZE=$(stat -c%s dist/pyright_worker.js 2>/dev/null || stat -f%z dist/pyright_worker.js 2>/dev/null)
        GZIP=$(gzip -c dist/pyright_worker.js | wc -c)
        printf "pyright_worker.js:  %s (%s gzipped)\n" "$(numfmt --to=iec $SIZE 2>/dev/null || echo ${SIZE}B)" "$(numfmt --to=iec $GZIP 2>/dev/null || echo ${GZIP}B)"
    else
        echo "pyright_worker.js:  not built (run 'just build')"
    fi
    if [ -f assets/typeshed-fallback.zip ]; then
        SIZE=$(stat -c%s assets/typeshed-fallback.zip 2>/dev/null || stat -f%z assets/typeshed-fallback.zip 2>/dev/null)
        printf "typeshed-fallback:  %s\n" "$(numfmt --to=iec $SIZE 2>/dev/null || echo ${SIZE}B)"
    else
        echo "typeshed-fallback:  not packed (run 'just pack-typeshed')"
    fi
