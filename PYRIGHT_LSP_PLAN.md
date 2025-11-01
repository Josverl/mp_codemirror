# Pyright LSP Integration Plan for CodeMirror

## Overview

This document outlines the plan to integrate Pyright LSP (Language Server Protocol) support into the CodeMirror 6 Python editor for MicroPython development.

## Architecture

### Current State
- Simple CodeMirror 6 editor with Python syntax highlighting
- Static HTML page deployable to GitHub Pages
- Basic editing features (line numbers, bracket matching, code folding)

### Target State
- LSP-powered Python editor with:
  - Real-time diagnostics (errors/warnings)
  - Intelligent autocompletion
  - Hover tooltips with type information
  - Go to definition
  - Find references
  - Signature help

## Implementation Approach

### Phase 1: Infrastructure Setup
**Goal**: Install dependencies and create LSP client foundation

**Tasks**:
1. Install `@codemirror/lsp-client` via npm/CDN
2. Create LSP client configuration
3. Set up mock transport for testing without server
4. Create basic LSP plugin integration

**Files to Create/Modify**:
- `src/lsp-client.js` - LSP client setup and configuration
- `src/lsp-mock-transport.js` - Mock transport for testing
- `src/app.js` - Integrate LSP extensions
- `src/index.html` - Add LSP client import

**Testing**:
- Verify LSP client initializes without errors
- Test mock transport sends/receives messages
- Confirm editor still works with LSP extensions

### Phase 2: Diagnostics (Error/Warning Highlighting)
**Goal**: Show Python syntax errors and type errors in the editor

**Tasks**:
1. Implement diagnostic provider
2. Add diagnostic decorations (squiggly underlines)
3. Display diagnostic tooltips on hover
4. Add diagnostic gutter markers

**CodeMirror Extensions**:
- `@codemirror/lint` - Already imported via LSP client
- Custom diagnostic conversion from LSP format

**LSP Messages**:
- `textDocument/publishDiagnostics` - Receive diagnostics from server

**Testing Strategy**:
```python
# Test cases:
1. Syntax error: missing colon
   def hello()
       print("world")

2. Undefined variable
   print(undefined_var)

3. Type error (if using type hints)
   x: int = "string"

4. Import error
   import non_existent_module
```

**Playwright Tests**:
- Load editor with error code
- Verify error underlines appear
- Hover over error, check tooltip
- Check gutter has error marker
- Fix error, verify diagnostics clear

### Phase 3: Autocompletion
**Goal**: Provide intelligent code suggestions as user types

**Tasks**:
1. Implement completion provider
2. Convert LSP completions to CodeMirror format
3. Handle completion triggers (., after import, etc.)
4. Add completion documentation in tooltips

**LSP Messages**:
- `textDocument/completion` - Request completions
- `completionItem/resolve` - Get full completion details

**CodeMirror Extensions**:
- Integrate with `@codemirror/autocomplete`

**Testing Strategy**:
```python
# Test cases:
1. Built-in completions
   import s|  # Should suggest sys, string, etc.

2. Member completions
   "hello".| # Should suggest upper, lower, split, etc.

3. Module member completions
   import sys
   sys.| # Should suggest argv, path, exit, etc.

4. Function parameter hints
   def greet(name: str, age: int):
       pass
   greet(|) # Should show parameter hints
```

**Playwright Tests**:
- Type trigger character (e.g., ".")
- Verify completion list appears
- Check completion items are relevant
- Select completion, verify it inserts correctly
- Test completion with partial text

### Phase 4: Hover Tooltips
**Goal**: Show type information and documentation on hover

**Tasks**:
1. Implement hover provider
2. Format hover content (Markdown to HTML)
3. Style hover tooltips
4. Handle multi-part hover information

**LSP Messages**:
- `textDocument/hover` - Request hover information

**Testing Strategy**:
```python
# Test cases:
1. Hover over built-in function
   print|("hello")  # Show print signature

2. Hover over variable
   x = 5
   print(x|)  # Show x: int

3. Hover over function
   def greet(name: str):
       """Say hello"""
       pass
   greet|()  # Show function signature + docstring

4. Hover over imported module
   import sys|  # Show module documentation
```

**Playwright Tests**:
- Hover over various code elements
- Verify tooltip appears
- Check tooltip content is correct
- Verify tooltip disappears on mouse out
- Test with Markdown formatting

### Phase 5: Additional LSP Features (Future)
- **Go to Definition** (F12)
- **Find References** (Shift+F12)
- **Rename Symbol** (F2)
- **Signature Help** (Ctrl+Shift+Space)
- **Document Symbols** (Outline view)
- **Formatting** (Shift+Alt+F)

## Technical Decisions

### LSP Server Deployment Options

#### Option 1: Mock/Client-Side (MVP for GitHub Pages)
**Pros**:
- Works on static GitHub Pages
- No server infrastructure needed
- Fast initial development
- Good for testing UI/UX

**Cons**:
- Limited LSP features
- No real type checking
- Can't handle complex imports

**Implementation**:
```javascript
class MockTransport {
  constructor() {
    this.handlers = [];
  }

  send(message) {
    // Parse message and generate mock responses
    const msg = JSON.parse(message);
    if (msg.method === 'textDocument/completion') {
      // Return mock completions
      this.handlers.forEach(h => h(JSON.stringify({
        id: msg.id,
        result: { items: [...mockCompletions] }
      })));
    }
  }

  subscribe(handler) {
    this.handlers.push(handler);
  }

  unsubscribe(handler) {
    const index = this.handlers.indexOf(handler);
    if (index > -1) this.handlers.splice(index, 1);
  }
}
```

#### Option 2: WebSocket Server (Full Features)
**Pros**:
- Full Pyright capabilities
- Real type checking
- Handles complex projects

**Cons**:
- Requires server infrastructure
- More complex deployment
- Network latency

**Implementation**:
```javascript
class WebSocketTransport {
  constructor(url) {
    this.ws = new WebSocket(url);
    this.handlers = [];
    
    this.ws.onmessage = (event) => {
      this.handlers.forEach(h => h(event.data));
    };
  }

  send(message) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    }
  }

  subscribe(handler) {
    this.handlers.push(handler);
  }

  unsubscribe(handler) {
    const index = this.handlers.indexOf(handler);
    if (index > -1) this.handlers.splice(index, 1);
  }
}
```

#### Option 3: Pyodide (Browser-Based Python)
**Pros**:
- Runs entirely in browser
- No server needed
- Can potentially run Pyright

**Cons**:
- Large download (several MB)
- Complex setup
- May not support all Pyright features
- Performance concerns

**Status**: Investigate for future phase

### Recommended Approach

**Phase 1 (MVP)**: Mock transport with basic features
- Allows UI/UX development and testing
- Works on GitHub Pages
- Foundation for real server integration

**Phase 2 (Production)**: WebSocket server
- Deploy simple WebSocket server
- Connect to real Pyright instance
- Full LSP features

**Phase 3 (Advanced)**: Investigate Pyodide
- For fully offline capability
- If Pyright can run in browser

## Dependencies

### NPM Packages (via CDN)
```json
{
  "@codemirror/lsp-client": "^latest",
  "@codemirror/lint": "^latest (peer dependency)",
  "@codemirror/autocomplete": "^latest (already installed)"
}
```

### Development Dependencies
```json
{
  "pytest": "^latest (already installed)",
  "pytest-playwright": "^latest (already installed)"
}
```

## File Structure

```
mp_codemirror/
├── src/
│   ├── index.html                 # Main HTML (modified)
│   ├── app.js                     # Main app (modified)
│   ├── styles.css                 # Styles (modified)
│   ├── lsp/
│   │   ├── client.js             # LSP client setup (new)
│   │   ├── mock-transport.js     # Mock transport (new)
│   │   ├── websocket-transport.js # WebSocket transport (new, future)
│   │   ├── diagnostics.js        # Diagnostics provider (new)
│   │   ├── completion.js         # Completion provider (new)
│   │   ├── hover.js              # Hover provider (new)
│   │   └── utils.js              # LSP utilities (new)
├── tests/
│   ├── test_lsp_diagnostics.py   # Diagnostics tests (new)
│   ├── test_lsp_completion.py    # Completion tests (new)
│   └── test_lsp_hover.py         # Hover tests (new)
└── docs/
    ├── LSP_SETUP.md              # LSP setup guide (new)
    └── PYRIGHT_SERVER.md         # Server deployment guide (new)
```

## Testing Strategy

### Unit Tests (JavaScript)
- Test LSP message formatting
- Test transport layer
- Test provider logic

### Integration Tests (Playwright)
- Test full LSP workflow
- Test UI interactions
- Test error handling

### Test-Driven Development Workflow
1. Write Playwright test for feature
2. Run test (should fail)
3. Implement feature incrementally
4. Test existing features (regression)
5. Run new test (should pass)
6. Refactor if needed
7. Repeat for next feature

## MicroPython Considerations

### Type Stubs
- Need MicroPython-specific type stubs
- Configure Pyright to use MicroPython stdlib instead of CPython
- Support device-specific modules (machine, esp32, etc.)

**Configuration** (future):
```json
{
  "pyrightconfig.json": {
    "stubPath": "./stubs/micropython",
    "typeshedPath": "./stubs/micropython/typeshed",
    "executionEnvironments": [{
      "name": "micropython",
      "extraPaths": ["./stubs/micropython-stdlib"]
    }]
  }
}
```

### Device Selection
- UI dropdown for target device (ESP32, RP2040, etc.)
- Load appropriate stubs based on selection
- Filter completions to device-specific APIs

## Timeline

### Week 1: Infrastructure
- [ ] Install @codemirror/lsp-client
- [ ] Create mock transport
- [ ] Set up LSP client
- [ ] Basic integration tests

### Week 2: Diagnostics
- [ ] Implement diagnostics provider
- [ ] Add diagnostic decorations
- [ ] Create diagnostic tests
- [ ] Test with various error types

### Week 3: Autocompletion
- [ ] Implement completion provider
- [ ] Handle completion triggers
- [ ] Create completion tests
- [ ] Test completion scenarios

### Week 4: Hover & Polish
- [ ] Implement hover provider
- [ ] Format hover content
- [ ] Create hover tests
- [ ] UI polish and bug fixes

## Success Criteria

### MVP Success
- ✅ Diagnostics show Python syntax errors
- ✅ Autocomplete suggests built-in functions
- ✅ Hover shows basic type information
- ✅ Works on GitHub Pages
- ✅ All features tested with Playwright

### Production Success
- ✅ Connected to real Pyright server
- ✅ Full LSP features (goto definition, references)
- ✅ MicroPython-specific completions
- ✅ Device-specific API filtering
- ✅ Fast, responsive UX

## Resources

### Documentation
- [LSP Specification](https://microsoft.github.io/language-server-protocol/)
- [Pyright Documentation](https://github.com/microsoft/pyright)
- [CodeMirror LSP Client](https://codemirror.net/docs/ref/#lsp-client)
- [MicroPython Documentation](https://docs.micropython.org/)

### Examples
- [CodeMirror LSP Example](https://github.com/codemirror/dev/tree/main/packages/lsp-client)
- [Monaco Editor LSP](https://github.com/microsoft/monaco-editor)
- [Thonny IDE](https://thonny.org/) - MicroPython IDE with LSP

## Notes

- Follow test-driven development as per copilot instructions
- Use Playwright for exploratory and automated testing
- Keep code modular for easy maintenance
- Document all decisions and rationale
- Test on multiple browsers (Chrome, Firefox, Safari)
