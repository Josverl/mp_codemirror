# Pyright LSP Integration Plan for CodeMirror

> **⚠️ CRITICAL REQUIREMENT**: This project MUST integrate with a real Pyright/Pylance LSP server. Mock implementations are only for initial development. Sprint 2 focuses on establishing this connection - no further feature work until real Pyright diagnostics are functional.

> **📌 GitHub Pages Note**: This requirement means the project can no longer be deployed as a static site. Server infrastructure is required.

## Overview

This document outlines the plan to integrate **Pyright/Pylance LSP Server** support into the CodeMirror 6 MicroPython editor for MicroPython development.

**CRITICAL**: This plan requires a real Pyright LSP server running. Mock-only implementations are insufficient for production use.

## Architecture

### Current State
- Simple CodeMirror 6 editor with Python syntax highlighting
- Static HTML page deployable to GitHub Pages
- Basic editing features (line numbers, bracket matching, code folding)
- **Mock LSP transport** for initial testing (Phase 1 complete)

### Target State
- **Full Pyright LSP Server** connected via WebSocket
- Real-time diagnostics from Pyright
- Intelligent autocompletion with type information
- Hover tooltips with documentation
- Go to definition and find references
- MicroPython-specific type stubs

**Note**: GitHub Pages deployment may no longer be viable - will require server infrastructure for LSP server.

## Implementation Approach

### Sprint 1: Mock LSP Infrastructure (✅ COMPLETED)
**Status**: Complete - Mock transport, diagnostics display working

**Completed**:
- ✅ Created SimpleLSPClient for LSP protocol handling
- ✅ Created MockTransport for testing
- ✅ Implemented diagnostics display with lintGutter
- ✅ Fast, focused test suite (3 tests, ~8.5s)
- ✅ Verified diagnostic icons display correctly

### Sprint 2: Pyright LSP Server Integration (✅ COMPLETED)
**Goal**: Connect to real Pyright/Pylance LSP server and get actual diagnostics

**Status**: ✅ Complete - Pyright v1.1.407 integration working via WebSocket

**Critical Requirements**:
- **MUST** have Pyright LSP server running
- **MUST** establish WebSocket or stdio communication
- **MUST** receive real diagnostics from Pyright
- **MUST** verify with Python code containing actual errors

**Tasks**:
1. **Research & Design** (1-2 days)
   - Research Pyright server deployment options
   - Choose communication method (WebSocket vs stdio)
   - Design server architecture
   - Document hosting requirements
   
2. **Server Setup** (2-3 days)
   - Install Pyright/Pylance LSP server
   - Create WebSocket bridge (if needed)
   - Test server responds to LSP messages
   - Verify initialize/initialized handshake
   
3. **Client Integration** (2-3 days)
   - Create WebSocketTransport class
   - Replace MockTransport with WebSocketTransport
   - Test connection establishment
   - Verify LSP protocol messages flow
   
4. **Diagnostics Validation** (1-2 days)
   - Send real Python code to server
   - Receive actual Pyright diagnostics
   - Verify diagnostic display in editor
   - Test with multiple error types

**Testing Strategy**:
```python
# Real error tests with Pyright:
1. Undefined variable
   print(undefined_variable)  # Pyright: "undefined_variable" is not defined

2. Type mismatch
   x: int = "string"  # Pyright: Expression of type "str" cannot be assigned to "int"

3. Import error
   import non_existent  # Pyright: Import "non_existent" could not be resolved

4. Function signature mismatch
   def func(x: int): pass
   func("string")  # Pyright: Argument of type "str" cannot be assigned to parameter "x"
```

**Playwright Tests**:
- Load editor, verify server connection
- Type code with error, verify Pyright diagnostic appears
- Fix error, verify diagnostic clears
- Test multiple simultaneous errors
- Verify diagnostic messages match Pyright output

**Success Criteria**:
- ✅ Pyright server runs and responds
- ✅ WebSocket connection established
- ✅ Real diagnostics received from Pyright
- ✅ Diagnostics display correctly in editor
- ✅ All tests pass with real server

**Deliverables**:
- `src/lsp/websocket-transport.js` - WebSocket LSP transport
- `server/pyright-server.py` or `server/pyright-server.js` - Server wrapper
- Updated tests using real Pyright
- Documentation on server setup

### Sprint 3: Real-Time Diagnostics (✅ COMPLETED)
**Goal**: Provide instant feedback as user types with intelligent debouncing

**Status**: ✅ Complete - Debounced didChange notifications (300ms), comprehensive testing

**Completed**:
- ✅ Implemented debounced `textDocument/didChange` notifications
- ✅ Document version tracking for LSP protocol
- ✅ Automatic error display after typing pauses
- ✅ 8 comprehensive tests (100% passing)
- ✅ Exploratory and automated testing complete
- ✅ Documentation in README.md, TECHNICAL.md, SPRINT3_SUMMARY.md

**Refactoring & Optimization Notes**:
- Code is clean and maintainable
- Tests are fast and reliable
- WebSocket connection is stable
- Error handling is robust
- Mock LSP removed (production-ready)

### Sprint 4: Autocompletion with Pyright
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

### LSP Server Deployment - MANDATORY PYRIGHT

**Decision**: We MUST use a real Pyright/Pylance LSP server. Mock implementations are for initial development only.

#### Chosen Approach: WebSocket Bridge to Pyright Server

**Architecture**:
```
Browser (CodeMirror) 
  ↕ WebSocket
WebSocket Server (Node.js/Python)
  ↕ stdio/IPC
Pyright LSP Server (Node.js)
```

**Pros**:
- Full Pyright capabilities
- Real type checking and analysis
- MicroPython stubs support
- Accurate diagnostics
- Production-ready

**Cons**:
- Requires server infrastructure
- Can't run on GitHub Pages
- Need to manage server lifecycle
- Network latency considerations

**Implementation Options**:

**Option A: Node.js WebSocket Bridge**
```javascript
const WebSocket = require('ws');
const { spawn } = require('child_process');

const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
  // Spawn Pyright server for this connection
  const pyright = spawn('pyright-langserver', ['--stdio']);
  
  // Bridge messages
  ws.on('message', (data) => {
    pyright.stdin.write(data);
  });
  
  pyright.stdout.on('data', (data) => {
    ws.send(data);
  });
});
```

**Option B: Python WebSocket Bridge** (Recommended for MicroPython project)
```python
import asyncio
import websockets
import subprocess
import json

async def lsp_bridge(websocket):
    # Start Pyright server
    pyright = subprocess.Popen(
        ['pyright-langserver', '--stdio'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    
    async for message in websocket:
        # Forward to Pyright
        pyright.stdin.write(message.encode())
        pyright.stdin.flush()
        
        # Read response
        response = pyright.stdout.readline()
        await websocket.send(response.decode())

start_server = websockets.serve(lsp_bridge, "localhost", 8080)
asyncio.get_event_loop().run_until_complete(start_server)
```

### Deployment Hosting Options

**Option 1: Local Development Server**
- Run server on localhost during development
- User must run server manually
- Good for initial testing

**Option 2: Cloud-Hosted Server**
- Deploy to Heroku, Railway, Fly.io, etc.
- Always available
- Multiple users can connect
- Cost considerations

**Option 3: Docker Container**
- Package server + Pyright in container
- Easy deployment
- Consistent environment
- User can run locally or in cloud

**Recommended**: Start with Option 1 (local), then move to Option 3 (Docker)
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

### Sprint 1: Mock LSP Infrastructure (✅ COMPLETED - 1 week)
- ✅ Install @codemirror/lint
- ✅ Create SimpleLSPClient
- ✅ Create MockTransport
- ✅ Implement diagnostics display
- ✅ Fast test suite (3 tests, ~8.5s)

### Sprint 2: Pyright LSP Server Integration (🚧 CURRENT - 2 weeks)
**Week 1: Research & Server Setup**
- [ ] Research Pyright deployment options
- [ ] Choose WebSocket vs stdio approach
- [ ] Set up Pyright server locally
- [ ] Create WebSocket bridge
- [ ] Test LSP initialize handshake

**Week 2: Client Integration & Testing**
- [ ] Create WebSocketTransport class
- [ ] Replace MockTransport in production
- [ ] Send real code to Pyright
- [ ] Receive and display real diagnostics
- [ ] Update tests for real server
- [ ] Document server setup

**Success Gate**: Real Pyright diagnostics displaying in editor

### Sprint 3: Refactoring & Optimization (1 week)
- [ ] Refactor LSP client error handling
- [ ] Optimize WebSocket reconnection
- [ ] Add connection status UI
- [ ] Handle server failures gracefully
- [ ] Performance optimization
- [ ] Code cleanup

### Sprint 4: Autocompletion (2 weeks)
- [ ] Implement completion provider
- [ ] Send textDocument/completion to Pyright
- [ ] Convert LSP completions to CodeMirror
- [ ] Handle completion triggers
- [ ] Test with real Pyright completions
- [ ] Create focused test suite

### Sprint 5: Hover Tooltips (1 week)
- [ ] Implement hover provider
- [ ] Send textDocument/hover to Pyright
- [ ] Format Markdown hover content
- [ ] Style tooltips
- [ ] Test with real Pyright hover info

### Sprint 6: MicroPython Stubs Integration (2 weeks)
- [ ] Research MicroPython type stubs
- [ ] Configure Pyright for MicroPython
- [ ] Add device-specific stubs (ESP32, RP2040)
- [ ] Test MicroPython completions
- [ ] Add device selector UI

### Sprint 7+: Additional Features (Future)
- [ ] Go to Definition
- [ ] Find References
- [ ] Rename Symbol
- [ ] Signature Help
- [ ] Document Formatting

## Current Status (Updated January 2025)

### Completed ✅
- **Sprint 1: Mock LSP Infrastructure**
  - SimpleLSPClient with full LSP protocol support
  - MockTransport for testing
  - Diagnostics display with lintGutter
  - Fast, focused test suite
  
- **Sprint 2: Pyright LSP Server Integration**
  - Pyright v1.1.407 via WebSocket (ws://localhost:9011/lsp)
  - WebSocketTransport implementation
  - jesse-ai/python-language-server bridge (git submodule)
  - Real diagnostics from Pyright working
  - VSCode tasks for easy server management
  - MicroPython stubs integration (micropython-stdlib-stubs)
  
- **Sprint 3: Real-Time Diagnostics**
  - Debounced `textDocument/didChange` (300ms)
  - Document version tracking
  - Automatic error display while typing
  - 8 comprehensive tests (100% passing)
  - Full documentation (README, TECHNICAL, SPRINT3_SUMMARY)
  - Mock LSP removed (production-ready)

### In Progress 🚧
- **Sprint 4: Autocompletion & Hover Tooltips** (Next)

### Next Steps
1. Implement `textDocument/completion` request
2. Create CodeMirror completion source
3. Implement `textDocument/hover` request
4. Format hover content (Markdown to HTML)
5. Test with MicroPython modules
6. Document new features

## Success Criteria

### Sprint 2 Success (Pyright Server)
- ✅ Pyright LSP server running locally
- ✅ WebSocket bridge functional
- ✅ Initialize/initialized handshake works
- ✅ Real Python code sent to server
- ✅ Actual Pyright diagnostics received
- ✅ Diagnostics display in editor
- ✅ Tests updated for real server
- ✅ Server setup documented

### MVP Success (After Sprint 5)
- ✅ Pyright diagnostics working
- ✅ Autocompletion from Pyright
- ✅ Hover tooltips from Pyright
- ✅ All features tested with real server
- ✅ Fast, reliable tests (<30s total)

### Production Success (After Sprint 6)
- ✅ MicroPython stubs integrated
- ✅ Device-specific completions
- ✅ Stable server deployment
- ✅ Documentation complete

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
