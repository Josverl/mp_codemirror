# CodeMirror 6 MicroPython Editor

A simple, static HTML5 application featuring a CodeMirror 6 editor configured for Python syntax highlighting. This project is designed to be deployed to GitHub Pages and serves as a foundation for future LSP integration with Pylance and MicroPython type stubs.

## Features

### Current (Phase 1 & 2)
- ✅ Python syntax highlighting
- ✅ Line numbers
- ✅ Dark/Light theme toggle
- ✅ Auto-indentation (4 spaces for Python)
- ✅ Bracket matching and auto-closing
- ✅ Code folding
- ✅ Multiple cursors/selections
- ✅ Search functionality (Ctrl/Cmd+F)
- ✅ Undo/Redo history
- ✅ Tab key support for indentation
- ✅ Responsive design (mobile-friendly)
- ✅ **LSP Integration** - Real Pyright v1.1.407 via WebSocket
- ✅ **Real-time Diagnostics** - Errors and warnings as you type (debounced 300ms)
- ✅ **Type Checking** - Full Python type analysis
- ✅ **Document Versioning** - Automatic version tracking for LSP updates

### Real-Time Diagnostics

The editor now provides **real-time feedback** on your Python code:

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

### Planned (Phase 2 - In Progress)
- � Autocompletion with type hints (LSP infrastructure ready)
- � Hover tooltips with documentation (LSP infrastructure ready)
- 🔲 Go to definition
- 🔲 Find references

### Planned (Phase 3)
- 🔲 MicroPython type stubs
- 🔲 Device-specific stubs (ESP32, RP2040, etc.)
- 🔲 Board selector for context-aware completions

## Project Structure

```
mp_codemirror/
├── .github/
│   └── copilot-instructions.md  # Agent instructions
├── .vscode/
│   └── tasks.json          # VSCode tasks for starting servers
├── src/
│   ├── lsp/                # LSP client implementation
│   │   ├── client.js       # Main LSP client setup
│   │   ├── websocket-transport.js  # WebSocket transport for Pyright
│   │   ├── diagnostics.js  # Diagnostics extension for CodeMirror
│   │   └── simple-client.js        # Simplified LSP client wrapper
│   ├── examples/           # Python example files
│   │   ├── examples.json   # List of example files
│   │   ├── blink_led.py    # LED blink example (default)
│   │   ├── espnow.py       # ESP-NOW example
│   │   └── temperature_sensor.py  # Temperature sensor example
│   ├── index.html          # Main HTML page
│   ├── styles.css          # Custom styling
│   └── app.js              # Application logic and CodeMirror setup
├── server/
│   ├── pyright-lsp-bridge/ # Git submodule: jesse-ai/python-language-server
│   │   ├── pyright-bridge.ts   # WebSocket bridge implementation
│   │   └── pyrightconfig.json  # Pyright configuration template
│   └── README.md           # Server documentation
├── tests/
│   ├── conftest.py         # Pytest configuration
│   ├── test_editor.py      # Editor tests with Playwright
│   └── README.md           # Testing documentation
└── README.md               # This file
```

## Getting Started

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd mp_codemirror
   ```

2. **Initialize the git submodule (LSP bridge):**
   ```bash
   git submodule update --init --recursive
   cd server/pyright-lsp-bridge
   npm install
   cd ../..
   ```

3. **Start the development servers:**

   **Option A: Using VSCode Tasks (Recommended):**
   - Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
   - Type "Tasks: Run Task"
   - Select "Start All Servers"
   - Both the LSP bridge and HTTP server will start automatically
   
   **Option B: Manual start:**
   
   Terminal 1 - LSP Bridge:
   ```bash
   cd server/pyright-lsp-bridge
   npm start
   ```
   
   Terminal 2 - HTTP Server:
   ```bash
   python -m http.server 8888
   ```

4. **Open in browser:**
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

### Architecture

- **No Build Step:** Uses ES modules loaded directly from CDN (esm.sh)
- **Module-based:** Modern ES6+ JavaScript with imports
- **CDN Provider:** esm.sh for CodeMirror packages
- **Browser Compatibility:** Modern browsers with ES module support

### Dependencies (via CDN)

All dependencies are loaded from CDN, no npm installation required:

- `codemirror@6.0.1` - Core editor
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
pip install pytest playwright pytest-playwright

# Install Playwright browsers
playwright install chromium
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

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

## Troubleshooting

### Editor doesn't load
- **Issue:** "Failed to fetch" errors in console
- **Solution:** Make sure you're using a web server, not opening the file directly

### Import errors
- **Issue:** Module resolution errors
- **Solution:** Check that import maps are supported in your browser, or update browser version

### Styling issues
- **Issue:** Editor looks broken
- **Solution:** Clear browser cache and reload, check browser console for CSS errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Resources

- [CodeMirror 6 Documentation](https://codemirror.net/6/)
- [CodeMirror 6 Examples](https://codemirror.net/examples/)
- [CodeMirror Discussion Forum](https://discuss.codemirror.net/)
- [Python Language Package](https://github.com/codemirror/lang-python)

## Roadmap

### Phase 1: Basic Editor ✅ (Complete)
- CodeMirror 6 setup with Python support
- Basic editing features
- Theme support

### Phase 2: LSP Integration ✅ (Complete - Basic Features)
- Browser-based LSP client ✅
- Pyright v1.1.407 integration via WebSocket ✅
- Real-time diagnostics ✅
- WebSocket transport layer ✅
- Autocompletion (in progress)
- Hover tooltips (in progress)

### Phase 3: MicroPython Support (Next)
- Custom type stubs for MicroPython
- Device-specific stubs
- Board selector UI

---

**Questions or Issues?** Open an issue on GitHub or check the [CodeMirror forum](https://discuss.codemirror.net/).
