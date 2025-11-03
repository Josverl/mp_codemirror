# Agent Instructions: CodeMirror Python Editor for GitHub Pages

You should not be overly optimistic, use icons sparingly.

## Project Overview

Build a simple, static HTML5 page hosting a CodeMirror 6 editor configured for Python syntax highlighting. 
It is preferable that the page can be deployed to GitHub Pages and serve as a foundation for future LSP integration with Pylance and MicroPython type stubs.
if it is needed to change the hosting infrastructure so that it cannot be run on github pages , that is acceptable 

the .ai_history folder contains previous documentation about this project, refer to them to avoid repeating work already done, or to get ideas on how to proceed.


## TESTING GUIDELINES
you MUST test your code thoroughly
tests should reside in the tests/ folder
Exploratory testing of web pages must be done using the Playwright MCP Server
Unit and integration testing should be based on Pytest + Playwright - but only start creating these after exploratory testing of a feature is complete


## Development servers
The development servers are defined in the .vscode/tasks.json file
- "Start LSP Bridge" - port 9011 - starts the LSP bridge server (pyright-lsp-bridge)
- "Start HTTP Server" - port 8888 - starts a simple HTTP server to serve the src/ folder

these tasks can be run concurrently for development.
The LSP bridge server can take a while to start up, so start it first.

## Python Environment Setup

### GitHub Copilot Agent Setup
The repository includes automated setup workflow in `.github/workflows/`:
- `copilot-setup-steps.yml` - Copilot agent environment setup

These workflows automatically:
1. Initialize and update git submodules recursively
2. Install `uv` package manager using astral-sh/setup-uv@v3
3. Install Python and project dependencies
4. Install MicroPython stubs to `typings/` directory
5. Cache environment for faster subsequent runs

### Local Development
use `uv` for environment management
use `uv pip` for package management
use `pytest` as the test runner

**Setup commands:**
```bash
# Install uv (if not already installed)
# Windows: irm https://astral.sh/uv/install.ps1 | iex
# Unix: curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize submodules
git submodule update --init --recursive

# Install dependencies
uv sync

# Install MicroPython stubs
uv pip install micropython-esp32-stubs --target typings
```

## Project Structure

```
d:\mypython\mp_codemirror\
├── .github/
│   └── copilot-instructions.md  # This file - Agent instructions
├── src/
│   ├── index.html      # Main HTML page
│   ├── styles.css      # Custom styling
│   └── app.js          # Application logic and CodeMirror setup
├── tests/
│   ├── conftest.py     # Pytest configuration and fixtures
│   ├── test_editor.py  # Playwright-based editor tests
│   └── README.md       # Testing documentation
└── README.md           # Project documentation
```

## Phase 1: Basic CodeMirror Setup (Current Phase)

### Requirements

1. **Single-page application** that works without a build step
2. **CodeMirror 6** loaded via CDN (ES modules)
3. **Python language support** only
4. **Basic features**:
   - Syntax highlighting for Python
   - Line numbers
   - Basic theme (light/dark toggle optional)
   - Auto-indentation
   - Bracket matching
   - Code folding

### Implementation Steps

#### Step 1: Create src/index.html
- Use modern HTML5 structure
- Import CodeMirror 6 via ES modules from CDN (unpkg or jsDelivr)
- Include a container div for the editor
- Link to external CSS and JS files

#### Step 2: Create src/app.js
- Import necessary CodeMirror packages:
  - `@codemirror/state`
  - `@codemirror/view` (EditorView, basicSetup)
  - `@codemirror/lang-python`
  - `@codemirror/theme-one-dark` (optional)
- Initialize EditorView with Python language support
- Configure basic editor extensions (line numbers, bracket matching, etc.)
- Add sample Python code as initial content

#### Step 3: Create src/styles.css
- Style the editor container (full viewport or configurable height)
- Add responsive design considerations
- Ensure proper font rendering (monospace font)

#### Step 4: Create README.md
- Document the project purpose
- Add setup/deployment instructions for GitHub Pages
- List current features and roadmap

### CodeMirror 6 Extensions to Include

```javascript
- basicSetup (from @codemirror/basic-setup or manual selection)
- python() (from @codemirror/lang-python)
- EditorView.lineWrapping (optional)
- bracketMatching()
- closeBrackets()
- indentOnInput()
- highlightActiveLineGutter()
- highlightActiveLine()
```

### Testing Checklist

- [ ] Page loads without errors in browser console
- [ ] Python syntax is highlighted correctly
- [ ] Line numbers display properly
- [ ] Typing and editing works smoothly
- [ ] Works on GitHub Pages after deployment

## Phase 2: LSP Integration (Future)

### Planned Architecture

1. **Browser-based LSP client**:
   - Use `vscode-languageclient/browser` or custom implementation
   - WebSocket or Web Worker communication

2. **Pylance LSP Server**:
   - Options:
     - Run Pylance in browser via Pyodide/WebAssembly (challenging)
     - Host Pylance server separately (requires backend)
     - Use alternative Python LSP (pyright standalone, python-lsp-server)

3. **CodeMirror LSP Extension**:
   - Create or integrate LSP extension for CodeMirror 6
   - Map LSP features to CodeMirror (diagnostics, completions, hover)

### LSP Features to Implement

- Autocompletion (LSP completionProvider)
- Hover tooltips (type information)
- Diagnostics (errors/warnings as inline markers)
- Go to definition
- Find references
- Signature help

### Design Considerations

- Keep static GitHub Pages deployment if possible
- If backend needed, document hosting requirements
- Consider WebAssembly-based solutions for client-only deployment

## Phase 3: MicroPython Type Stubs (Future)

### Requirements

1. **Custom type stubs** for MicroPython stdlib
2. **Device-specific stubs** (ESP32, RP2040, etc.)
3. **LSP configuration** to prioritize MicroPython stubs over CPython

### Implementation Strategy

1. **Stub sources**:
   - Use existing MicroPython stubs (micropython-stubs, Thonny, etc.)
   - Generate stubs from MicroPython firmware documentation
   - Maintain custom stub repository

2. **LSP Integration**:
   - Configure Pylance/Pyright to use MicroPython stubs
   - Set `python.analysis.stubPath` or equivalent
   - Disable incompatible CPython stdlib stubs

3. **UI Enhancements**:
   - Board/firmware selector dropdown
   - Dynamic stub loading based on target
   - Documentation links for MicroPython-specific APIs

### Testing Strategy

- Test completion for MicroPython-specific modules (machine, micropython, etc.)
- Verify CPython-only modules are not suggested
- Test device-specific APIs (ESP32 vs RP2040)

## Development Guidelines

### Code Style

- Use modern ES6+ JavaScript (ES modules)
- Prefer async/await over callbacks
- Keep functions small and focused
- Add comments for complex logic

### Git Workflow

- Main branch: stable, deployable code
- Feature branches for new functionality
- Clear commit messages following conventional commits

### GitHub Pages Deployment

1. Enable GitHub Pages in repository settings
2. Deploy from main branch, root directory or /docs folder
3. Test with `https://<username>.github.io/<repo-name>/`

### Performance Considerations

- Lazy-load LSP features (Phase 2+)
- Debounce expensive operations (diagnostics, completions)
- Use Web Workers for background processing
- Minimize bundle size (use CDN for CodeMirror)

## Resources

### Documentation
- CodeMirror 6: https://codemirror.net/6/
- Pylance: https://github.com/microsoft/pylance-release
- Pyright: https://github.com/microsoft/pyright
- LSP Specification: https://microsoft.github.io/language-server-protocol/

### Existing Projects
- Monaco Editor (reference for LSP integration)
- JupyterLab CodeMirror (Python editor example)
- Browser-based Python IDEs (Pyodide, Skulpt)

## Notes for AI Agent

- Start with Phase 1 only - simple, working solution
- Use CDN links to avoid build complexity
- Prioritize GitHub Pages compatibility
- Document all design decisions
- Keep code modular for future LSP integration
- Test in multiple browsers (Chrome, Firefox, Safari)
- When implementing LSP, research current browser-based solutions first
