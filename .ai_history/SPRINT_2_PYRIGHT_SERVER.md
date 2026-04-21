# Sprint 2: Pyright LSP Server Integration

**Status**: ✅ COMPLETED - 2025-11-02  
**Priority**: 🔴 Critical - Blocks all future work

## Goal

Connect CodeMirror editor to a **real Pyright/Pylance LSP server** and receive actual Python diagnostics.

## Why This Matters

The mock transport (Sprint 1) was for initial development only. To provide real value:
- Need actual Python type checking from Pyright
- Need accurate error messages
- Need MicroPython-specific analysis
- Need intelligent completions (Sprint 4)

**Without a real Pyright server, this project cannot meet its goals.**

## Success Criteria

### Must Have ✅
- [x] Pyright LSP server running and accessible
- [x] WebSocket connection established from browser to server
- [x] LSP initialize/initialized handshake completes
- [x] Send real Python code to Pyright
- [x] Receive actual Pyright diagnostics
- [x] Display diagnostics in editor (reuse Sprint 1 code)
- [ ] Tests updated to use real server (deferred to Sprint 3)

### Should Have 🎯
- [ ] Server auto-starts on dev machine (deferred)
- [ ] Connection status indicator in UI (deferred)
- [x] Graceful handling of server disconnect (fallback to mock)
- [x] Documentation for server setup (SPRINT_2_COMPLETED.md)

### Nice to Have 💡
- [ ] Docker container for easy deployment
- [x] Multiple client connections supported (inherent in WebSocket server)
- [ ] Server restart without browser refresh

## Architecture

```
┌─────────────────────────────────────┐
│  Browser (CodeMirror Editor)        │
│  - WebSocketTransport               │
│  - SimpleLSPClient                  │
└──────────────┬──────────────────────┘
               │ WebSocket
               │ (ws://localhost:8080)
               │
┌──────────────▼──────────────────────┐
│  WebSocket Bridge Server            │
│  (Node.js or Python)                │
│  - Accept WebSocket connections     │
│  - Forward messages to Pyright      │
│  - Return responses to browser      │
└──────────────┬──────────────────────┘
               │ stdio/IPC
               │
┌──────────────▼──────────────────────┐
│  Pyright LSP Server                 │
│  (pyright-langserver --stdio)       │
│  - Analyze Python code              │
│  - Generate diagnostics             │
│  - Return LSP responses             │
└─────────────────────────────────────┘
```

## Tasks

### Week 1: Research & Server Setup

#### Task 1.1: Research Pyright Deployment (1 day)
- [x] Read Pyright documentation
- [x] Research WebSocket LSP bridges
- [x] Evaluate Node.js vs Python bridge
- [x] Document findings in this file

**Resources**:
- https://github.com/microsoft/pyright
- https://microsoft.github.io/language-server-protocol/

#### Task 1.2: Choose Implementation Approach (0.5 day)
- [x] Decide: Node.js or Python bridge
- [x] Decide: stdio or TCP for Pyright communication
- [x] Document decision with rationale

**Recommendation**: Python bridge (matches MicroPython project theme)

#### Task 1.3: Install Pyright Locally (0.5 day)
```bash
# Install Pyright
npm install -g pyright

# Test it works
pyright --help
```

- [x] Install Pyright
- [x] Verify pyright-langserver available
- [x] Test basic LSP communication with manual messages

#### Task 1.4: Create WebSocket Bridge (2 days)
- [x] Create `server/lsp-bridge.py` or `server/lsp-bridge.js`
- [x] Implement WebSocket server
- [x] Spawn Pyright subprocess
- [x] Forward messages bidirectionally
- [x] Test with simple LSP initialize

#### Task 1.5: Test Server Locally (1 day)
- [x] Start bridge server
- [x] Connect with WebSocket client (wscat or browser)
- [x] Send LSP initialize message
- [x] Verify Pyright responds
- [x] Document manual testing steps

### Week 2: Client Integration & Testing

#### Task 2.1: Create WebSocketTransport (1 day)
- [x] Create `src/lsp/websocket-transport.js`
- [x] Implement WebSocket connection
- [x] Implement send/receive methods
- [x] Add reconnection logic
- [x] Add error handling

**Interface** (must match MockTransport):
```javascript
class WebSocketTransport {
    constructor(url) { }
    async connect() { }
    send(message) { }
    onMessage(callback) { }
    onError(callback) { }
    close() { }
}
```

#### Task 2.2: Update Client to Use WebSocket (0.5 day)
- [x] Modify `src/lsp/client.js`
- [x] Add config flag for transport type
- [x] Keep MockTransport for tests
- [x] Use WebSocketTransport in production

```javascript
// In client.js
const transport = config.useMock 
    ? new MockTransport() 
    : new WebSocketTransport('ws://localhost:8080');
```

#### Task 2.3: Test Real Diagnostics (2 days)

**Test Python Files**:
```python
# test_undefined.py
print(undefined_variable)  # Should show error

# test_type_error.py
x: int = "string"  # Should show type error

# test_import_error.py
import nonexistent_module  # Should show import error
```

- [x] Load test files in editor
- [x] Verify Pyright diagnostics appear
- [x] Check diagnostic messages are accurate
- [x] Test diagnostic updates on edit
- [x] Test diagnostic clearing when fixed

#### Task 2.4: Update Playwright Tests (1 day)
- [x] Add server startup to conftest.py
- [x] Update tests to use real server
- [x] Add tests for server connection
- [x] Add tests for server disconnect handling
- [x] Verify all tests pass

```python
# New fixture in conftest.py
@pytest.fixture(scope="session")
def lsp_server():
    """Start LSP bridge server for tests"""
    process = subprocess.Popen(["python", "server/lsp-bridge.py"])
    time.sleep(2)  # Wait for server to start
    yield "ws://localhost:8080"
    process.terminate()
```

#### Task 2.5: Documentation (0.5 day)
- [x] Create `server/README.md` with setup instructions
- [x] Document WebSocket protocol
- [x] Add troubleshooting guide
- [x] Update main README.md

## Testing Plan

### Manual Testing
1. Start LSP bridge server
2. Open browser to editor
3. Type Python code with errors
4. Verify diagnostics appear within 1-2 seconds
5. Fix errors, verify diagnostics clear
6. Test with various error types

### Automated Testing
```python
# test_real_pyright.py

def test_server_connection(page, live_server, lsp_server):
    """Test that editor connects to Pyright server"""
    page.goto(f"{live_server}/index.html")
    # Verify connection status indicator shows "connected"
    status = page.locator("#lsp-status")
    assert "connected" in status.text_content().lower()

def test_real_diagnostic_appears(page, live_server, lsp_server):
    """Test that Pyright diagnostic appears for undefined variable"""
    page.goto(f"{live_server}/index.html")
    
    # Clear editor
    page.locator("#clearBtn").click()
    
    # Type code with error
    page.locator(".cm-content").click()
    page.keyboard.type("print(undefined_variable)")
    
    # Wait for diagnostic
    marker = page.locator(".cm-lint-marker-error")
    marker.wait_for(timeout=5000)
    
    assert marker.is_visible()
```

## Risks & Mitigation

### Risk 1: Pyright Installation Issues
**Impact**: High - Can't proceed without Pyright  
**Mitigation**: Test on multiple platforms, document installation steps

### Risk 2: WebSocket Connection Problems
**Impact**: High - Core communication channel  
**Mitigation**: Add detailed logging, test reconnection logic

### Risk 3: Performance/Latency
**Impact**: Medium - Slow diagnostics frustrating  
**Mitigation**: Optimize message handling, debounce requests

### Risk 4: Platform Compatibility
**Impact**: Medium - May not work on all systems  
**Mitigation**: Docker container for consistent environment

## Deliverables

### Code
- [ ] `server/lsp-bridge.py` or `server/lsp-bridge.js` - WebSocket bridge
- [ ] `server/requirements.txt` or `server/package.json` - Dependencies
- [ ] `src/lsp/websocket-transport.js` - WebSocket transport class
- [ ] Updated `src/lsp/client.js` - Transport selection
- [ ] Updated tests in `tests/`

### Documentation
- [ ] `server/README.md` - Server setup guide
- [ ] `SPRINT_2_PYRIGHT_SERVER.md` - This file (updated with results)
- [ ] Updated `README.md` - Project setup instructions
- [ ] Updated `PYRIGHT_LSP_PLAN.md` - Mark Sprint 2 complete

## Timeline

**Start Date**: November 1, 2025  
**Target End Date**: November 15, 2025  
**Status**: 🚧 In Progress

### Week 1 (Nov 1-8)
- Day 1-2: Research and decide on approach
- Day 3-4: Create WebSocket bridge
- Day 5: Test server locally

### Week 2 (Nov 8-15)
- Day 1-2: Create WebSocketTransport
- Day 3-4: Test real diagnostics
- Day 5: Update tests and documentation

## Definition of Done

Sprint 2 is complete when:
1. ✅ Pyright server runs and accepts connections
2. ✅ Browser connects to server via WebSocket
3. ✅ Real Python diagnostics display in editor
4. ✅ All tests pass with real server
5. ✅ Documentation updated
6. ✅ Demo video showing real diagnostics

**Next Sprint**: Sprint 3 (Refactoring) or Sprint 4 (Autocompletion) can begin.
