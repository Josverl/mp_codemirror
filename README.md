# CodeMirror 6 MicroPython Editor

A static HTML5 application featuring a CodeMirror 6 editor with full LSP support via Pyright running in a Web Worker. Includes MicroPython board-specific type stubs (ESP32, RP2040, STM32) with live switching. Deploys to GitHub Pages as static files — no server needed for LSP features.

## Features

### Current 
- ✅ Tablestakes CodeMirror functionality 
   - ✅ Line numbers
   - ✅ Dark/Light theme toggle
   - ✅ Auto-indentation (4 spaces for Python)
   - ✅ Bracket matching and auto-closing
   - ✅ Code folding
   - ✅ Multiple cursors/selections
   - ✅ Search functionality (Ctrl/Cmd+F)
   - ✅ Undo/Redo history
   - ✅ Tab key support for indentation
   - ✅ Responsive design (though the current layout is bad 😁)
- ✅ **MicroPython** syntax highlighting
- ✅ **LSP Integration** - Pyright running in a Web Worker (no server needed)
- ✅ **Real-time Diagnostics** - Errors and warnings as you type (debounced 300ms)
- ✅ **Type Checking** - Full Python type analysis
- ✅ **Document Versioning** - Automatic version tracking for LSP updates
- ✅ **Board Selector** - Switch between ESP32, RP2040, STM32 stubs

### Real-Time Diagnostics

The editor provides **real-time feedback** on your MicroPython code:

- **Instant Error Detection:** Syntax errors, undefined variables, and import issues are highlighted as you type
- **Smart Debouncing:** Changes are sent to the LSP server after 300ms of inactivity to prevent overwhelming the server
- **Visual Feedback:** Errors appear with red squiggly underlines directly in the editor
- **Performance Optimized:** Document version tracking ensures efficient updates
- **Automatic Updates:** Diagnostics refresh automatically when you fix errors

**How it works:**
1. Type Python code in the editor
2. After 300ms of no typing, a `textDocument/didChange` notification is sent to Pyright
3. Pyright analyzes your code and returns diagnostics
4. Errors and warnings are displayed inline with visual markers

**Keyboard Tip:** Keep typing without interruption - diagnostics will appear shortly after you pause.

### LSP-Powered Autocompletion

The editor provides **intelligent code completion** using Pyright's Language Server Protocol:

- **Context-Aware Suggestions:** Completions for imports, stdlib modules, and MicroPython APIs
- **Type-Based Icons:** Visual indicators for functions (ƒ), variables (𝑥), classes (○), and keywords (🔑)
- **Attribute Access:** Smart completion after dots (e.g., `sys.` shows all sys module members)
- **Automatic & Manual Trigger:** Completions appear as you type or via Ctrl+Space

**Examples:**
- Type `import o` → See available modules (os, opcode, operator, etc.)
- Type `sys.` → See all sys module attributes (platform, argv, exit, etc.)
- Type `"text".` → See all string methods (upper, lower, split, etc.)
- Type `pin.` (MicroPython) → See Pin methods (on, off, toggle, IRQ_RISING, etc.)

**Tested Coverage:**
- ✅ Python 3.11 stdlib - 96+ completions for sys module
- ✅ Import suggestions - 92 importable modules
- ✅ String methods - 85 str methods
- ✅ MicroPython - 54 machine.Pin members

**Technical Details:** See [SPRINT4_SUMMARY.md](.ai_history/SPRINT4_SUMMARY.md) for the complete implementation journey.

### LSP-Powered Hover Tooltips

The editor displays **rich documentation on hover** using Pyright's type analysis:

- **Type Information:** See variable types and class definitions instantly
- **Function Signatures:** View parameters, return types, and descriptions
- **Comprehensive Docstrings:** Full documentation from Python and MicroPython libraries
- **External Links:** Clickable links to official MicroPython documentation
- **Dual Theme Support:** Readable tooltips in both light and dark modes

**Examples:**
- Hover over `Pin` → See complete class documentation with all parameters
- Hover over `machine` → See module description with link to docs.micropython.org
- Hover over `led` variable → See Pin class type information
- Hover over any function → See signature and docstring

**What You'll See:**
- **(class) Pin** - Class type with full constructor documentation
- **(module) machine** - Module info with external documentation links
- **(function) sleep_ms** - Function signature and usage notes
- Type annotations, parameter descriptions, and usage examples

**Technical Details:**
- Uses CodeMirror's `hoverTooltip` extension
- LSP `textDocument/hover` requests to Pyright
- Markdown rendering with code block support
- Max width 500px, max height 400px, scrollable for long docs
- 98% opacity for excellent readability

### Planned (Future)
- 🔲 Go to definition
- 🔲 Find references

### Complete (Phase 3)
- ✅ MicroPython type stubs (ESP32, RP2040, STM32)
- ✅ Device-specific stubs switchable via board selector dropdown
- ✅ Board switching with live re-analysis

### Current (Phase 4)
- Testing, CI, and code quality improvements
- Pytest test tiers: unit, editor, worker, lsp

## Project Structure

```
mp_codemirror/
├── .github/
│   ├── copilot-instructions.md  # Agent instructions
│   └── workflows/
│       ├── test.yml             # CI test workflow
│       └── deploy.yml           # GitHub Pages deployment
├── .vscode/
│   └── tasks.json          # VSCode tasks for dev servers
├── src/
│   ├── lsp/                # LSP client implementation
│   │   ├── client.js       # Main LSP client setup
│   │   ├── worker-transport.js     # Web Worker transport
│   │   ├── transport-factory.js    # Transport factory
│   │   ├── diagnostics.js  # Diagnostics extension for CodeMirror
│   │   ├── completion.js   # Autocompletion integration
│   │   ├── hover.js        # Hover tooltips integration
│   │   └── simple-client.js        # LSP protocol client wrapper
│   ├── worker/             # Pyright Web Worker source
│   │   └── pyright-worker.ts       # Worker entry point (bundled to dist/)
│   ├── examples/           # Python example files
│   │   ├── examples.json   # List of example files
│   │   ├── blink_led.py    # LED blink example (default)
│   │   ├── espnow.py       # ESP-NOW example
│   │   ├── rp2_pio.py      # RP2040 PIO example
│   │   └── temperature_sensor.py  # Temperature sensor example
│   ├── index.html          # Main HTML page
│   ├── styles.css          # Custom styling
│   └── app.js              # Application logic and CodeMirror setup
├── dist/
│   └── pyright_worker.js   # Built Pyright worker (via webpack)
├── assets/
│   └── stubs-manifest.json # Board stubs manifest
├── scripts/
│   ├── pack-typeshed.mjs   # Pack typeshed for browser use
│   └── pack-stubs.mjs      # Pack MicroPython stubs per board
├── tests/
│   ├── conftest.py         # Pytest configuration and fixtures
│   ├── test_editor.py      # Editor UI tests (Playwright)
│   ├── test_worker_transport.py  # Web Worker transport tests
│   ├── test_lsp_features.py     # LSP feature tests
│   ├── test_lsp_diagnostics.py  # Diagnostics tests
│   └── README.md           # Testing documentation
├── typings/                # MicroPython type stubs
├── justfile                # Build and dev task runner
├── webpack.config.cjs      # Webpack config for worker build
└── README.md               # This file
```

## Getting Started

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd mp_codemirror
   ```

2. **Install dependencies:**
   ```bash
   git submodule update --init --recursive
   npm install --ignore-scripts
   uv sync
   ```

3. **Build the Pyright Web Worker:**
   ```bash
   just build
   ```
   This bundles Pyright, typeshed, and MicroPython stubs into `dist/pyright_worker.js`.

4. **Start the HTTP server:**
   ```bash
   just http
   # or: python -m http.server 8888
   ```
   No LSP bridge server is needed — Pyright runs in the browser via a Web Worker.

5. **Open in browser:**
   Navigate to `http://localhost:8888/src/`

### GitHub Pages Deployment

1. **Enable GitHub Pages:**
   - Go to your repository settings
   - Navigate to "Pages" section
   - Select "Deploy from a branch"
   - Choose `main` branch and `/src` folder
   - Click "Save"

2. **Access your editor:**
   Your editor will be available at:
   ```
   https://<username>.github.io/<repository-name>/
   ```

## Usage

### Basic Operations

- **Write Code:** Simply start typing Python code in the editor
- **Toggle Theme:** Click the 🌓 button to switch between dark and light themes
- **Clear Editor:** Click "Clear" to remove all content
- **Load Sample:** Click "Load Sample" to load example Python code from the `src/examples/` folder

The editor loads `examples/blink_led.py` by default on startup. You can add more example files to the `examples/` folder and they will be available for loading.

### Keyboard Shortcuts

| Action | Windows/Linux | macOS |
|--------|---------------|-------|
| Save | Ctrl+S | Cmd+S |
| Find | Ctrl+F | Cmd+F |
| Replace | Ctrl+H | Cmd+Alt+F |
| Undo | Ctrl+Z | Cmd+Z |
| Redo | Ctrl+Y | Cmd+Shift+Z |
| Toggle Comment | Ctrl+/ | Cmd+/ |
| Indent | Tab | Tab |
| Dedent | Shift+Tab | Shift+Tab |
| Toggle Fold | Ctrl+Shift+[ | Cmd+Alt+[ |
| Select All | Ctrl+A | Cmd+A |

## Technical Details

For architecture diagrams, integration guide, and detailed documentation see the [docs/](docs/) folder:

- [Architecture](docs/architecture.md) — component diagrams, LSP communication flow, build pipeline
- [Showcase](docs/showcase.md) — demo walkthrough, video script, micropython-stubs advantages, integration guide
- [Quick Start](docs/quickstart.md) — get running in 4 steps
- [Technical](docs/technical.md) — CDN dependency pinning details
- [Contributing](docs/contributing.md) — development setup and guidelines

### Architecture

- **No Build Step for UI:** CodeMirror loaded via ES modules from CDN (esm.sh)
- **Web Worker for LSP:** Pyright runs in a Web Worker (`dist/pyright_worker.js`), built via webpack
- **Board Switching:** ESP32, RP2040, STM32 stubs, switchable via dropdown
- **Static Deployment:** Full LSP features work on GitHub Pages — no server needed
- **Module-based:** Modern ES6+ JavaScript with imports

### Dependencies (via CDN)

All dependencies are loaded from CDN, no npm installation required:

- `codemirror@6.0.2` - Core editor
- `@codemirror/view` - Editor view
- `@codemirror/state` - Editor state management
- `@codemirror/language` - Language support
- `@codemirror/commands` - Editor commands
- `@codemirror/search` - Search functionality
- `@codemirror/autocomplete` - Autocompletion system
- `@codemirror/lint` - Linting support
- `@codemirror/lang-python` - Python language mode
- `@lezer/highlight` - Syntax highlighting

**Important:** To avoid version conflicts when using CodeMirror packages from CDN, we use the `?deps=` parameter to explicitly pin shared dependencies to the same versions across all packages. This prevents the "multiple instances of @codemirror/state" error that occurs when different packages load incompatible versions.

See `src/index.html` for the complete import map with dependency pinning.

### Browser Requirements

- Chrome/Edge 89+
- Firefox 89+
- Safari 15+
- Any browser with ES module support and import maps

## Testing

### Prerequisites

```bash
# Install Python dependencies
uv sync

# Install Playwright browsers
playwright install chromium
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run by tier
pytest tests/ -m unit -v          # Unit tests
pytest tests/ -m editor -v        # Editor/UI tests (Playwright)
pytest tests/ -m worker -v        # Web Worker tests
pytest tests/ -m lsp -v           # LSP feature tests

# Run with browser visible
pytest tests/ --headed

# Run specific test
pytest tests/test_editor.py::test_page_loads -v
```

The test suite covers:
- Editor initialization
- Python syntax highlighting
- Text editing operations
- Theme switching
- Button functionality
- Responsive layout
- No JavaScript errors

## Development Guidelines

### Code Style
- Python code 
    - ruff, typed 
- JavaScript 
    - Modern ES6+ JavaScript
    - Use `const`/`let`, avoid `var`
    - Prefer arrow functions
    - Use async/await over callbacks
    - Keep functions small and focused
    - Add JSDoc comments for public APIs

### Making Changes

1. Test locally first
2. Verify in multiple browsers if possible
3. Check console for errors
4. Test on mobile viewport
5. Commit with clear messages

### Future Extensions

When adding new features:
1. Keep static deployment in mind
2. Document any new dependencies
3. Update tests
4. Update this README
5. Consider LSP integration compatibility
## Contributing

See [docs/contributing.md](docs/contributing.md) for development setup, testing, and contribution guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Resources

- [Micropython Stubs](https://github.com/josverl/micropython-stubs)
- [Pyright](https://github.com/microsoft/pyright#static-type-checker-for-python)
- [CodeMirror 6 Documentation](https://codemirror.net/6/)
- [Python Language Package](https://github.com/codemirror/lang-python)
- [Micropython documentation](https://docs.micropython.org)
