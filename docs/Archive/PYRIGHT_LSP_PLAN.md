# Pyright LSP Integration Plan for CodeMirror

> **✅ CRITICAL REQUIREMENT ACHIEVED**: This project successfully integrates with a real Pyright/Pylance LSP server. Real-time diagnostics are fully functional through Sprint 3.

> **📌 Infrastructure Note**: The project uses a WebSocket bridge server (pyright-lsp-bridge) for LSP communication. GitHub Pages deployment is no longer viable.

## Overview

This document outlines the plan to integrate **Pyright/Pylance LSP Server** support into the CodeMirror 6 MicroPython editor for MicroPython development.

**STATUS**: Core LSP integration complete. Real Pyright diagnostics working with debounced real-time updates.

## Architecture

### Current State (✅ COMPLETED)
- CodeMirror 6 editor with Python syntax highlighting
- **Real Pyright LSP Server** connected via WebSocket
- Real-time diagnostics from Pyright with intelligent debouncing
- Production-ready WebSocket transport
- Comprehensive test suite (8 tests, 100% passing)
- MicroPython stubs integrated

### Target State (Remaining Work)
- Intelligent autocompletion with type information
- Hover tooltips with documentation
- Go to definition and find references
- Enhanced MicroPython-specific features

## Implementation Status

### Sprint 1: Mock LSP Infrastructure (✅ COMPLETED)
**Status**: ✅ Complete - Mock transport, diagnostics display working

**Completed Tasks**:
- ✅ Created SimpleLSPClient for LSP protocol handling
- ✅ Created MockTransport for testing
- ✅ Implemented diagnostics display with lintGutter
- ✅ Fast, focused test suite (3 tests, ~8.5s)
- ✅ Verified diagnostic icons display correctly

### Sprint 2: Pyright LSP Server Integration (✅ COMPLETED)
**Status**: ✅ Complete - Pyright v1.1.407 integration working via WebSocket

**Completed Tasks**:
- ✅ Research & Design completed
- ✅ Server Setup: Pyright LSP server deployed via WebSocket
- ✅ Client Integration: WebSocketTransport class implemented
- ✅ Diagnostics Validation: Real Pyright diagnostics working
- ✅ jesse-ai/python-language-server bridge integrated (git submodule)
- ✅ VSCode tasks for server management
- ✅ Server runs on ws://localhost:9011/lsp
- ✅ MicroPython stubs integrated (micropython-stdlib-stubs)

**Deliverables Completed**:
- ✅ `src/lsp/websocket-transport.js` - WebSocket LSP transport
- ✅ `jesse-ai/python-language-server` submodule - Server wrapper
- ✅ Updated tests using real Pyright
- ✅ Documentation on server setup

### Sprint 3: Real-Time Diagnostics (✅ COMPLETED)
**Status**: ✅ Complete - Debounced didChange notifications (300ms), comprehensive testing

**Completed Tasks**:
- ✅ Implemented debounced `textDocument/didChange` notifications
- ✅ Document version tracking for LSP protocol
- ✅ Automatic error display after typing pauses
- ✅ 8 comprehensive tests (100% passing)
- ✅ Exploratory and automated testing complete
- ✅ Documentation in README.md, TECHNICAL.md, SPRINT3_SUMMARY.md
- ✅ Mock LSP removed (production-ready)
- ✅ Code optimization and refactoring completed

**Testing Results**:
- ✅ Real error detection: undefined variables, type mismatches
- ✅ Import error handling
- ✅ Function signature validation
- ✅ Performance optimized with 300ms debouncing

### Sprint 10: Autocompletion Integration (✅ COMPLETED)
**Goal**: Provide intelligent code suggestions from Pyright as user types

**Remaining Tasks**:
1. **Completion Provider Implementation** (2-3 days)
   - Implement `textDocument/completion` LSP request
   - Create CodeMirror completion source adapter
   - Handle completion triggers (., after import, etc.)
   - Map LSP completion items to CodeMirror format

2. **Completion UI Integration** (1-2 days)
   - Integrate with `@codemirror/autocomplete`
   - Style completion popup
   - Add completion documentation tooltips
   - Handle keyboard navigation

3. **Testing & Validation** (1-2 days)
   - Test built-in function completions
   - Test member completions (`"hello".|`)
   - Test module member completions (`sys.|`)
   - Test MicroPython-specific completions
   - Automated Playwright tests

**LSP Messages to Implement**:
- `textDocument/completion` - Request completions
- `completionItem/resolve` - Get full completion details (optional)

**Success Criteria**:
- [x] Typing trigger characters shows completion popup
- [x] Completions are relevant to context
- [x] MicroPython modules show correct completions
- [x] Performance is responsive (<200ms)
- [x] All tests pass

### Sprint 11: Hover Tooltips (✅ COMPLETED)
**Goal**: Show type information and documentation on hover

**Remaining Tasks**:
1. **Hover Provider Implementation** (2-3 days)
   - Implement `textDocument/hover` LSP request
   - Handle hover positioning and timing
   - Format hover content (Markdown to HTML)
   - Style hover tooltips consistently

2. **Content Formatting** (1-2 days)
   - Parse Markdown hover responses from Pyright
   - Render type signatures attractively
   - Display docstrings with proper formatting
   - Handle multi-part hover information

3. **Testing & Polish** (1-2 days)
   - Test hover over variables, functions, imports
   - Test with MicroPython-specific elements
   - Verify tooltip positioning and behavior
   - Performance optimization

**LSP Messages to Implement**:
- `textDocument/hover` - Request hover information

**Success Criteria**:
- [x] Hover shows type information for variables
- [x] Function signatures display correctly
- [x] Docstrings render with Markdown formatting
- [x] MicroPython module documentation appears
- [x] Tooltips position correctly and disappear appropriately

### Sprint 12: Advanced LSP Features (📋 FUTURE)
**Goal**: Add navigation and refactoring capabilities

**Remaining Features**:
- **Go to Definition** (F12)
  - `textDocument/definition` LSP request
  - Navigate to symbol definitions
  - Handle cross-file navigation
  
- **Find References** (Shift+F12)
  - `textDocument/references` LSP request
  - Display references in side panel or overlay
  - Navigate between references
  
- **Rename Symbol** (F2)
  - `textDocument/rename` LSP request
  - Rename across files
  - Preview changes before applying
  
- **Signature Help** (Ctrl+Shift+Space)
  - `textDocument/signatureHelp` LSP request
  - Show function parameter hints
  - Highlight current parameter

### Sprint 13: MicroPython Enhancement (📋 FUTURE)
**Goal**: Optimize experience for MicroPython development

**Remaining Tasks**:
- **Device Selection UI**
  - Dropdown for target device (ESP32, RP2040, etc.)
  - Load device-specific stubs dynamically
  - Filter completions to device APIs
  
- **MicroPython Stubs Optimization**
  - Expand stub coverage for more devices
  - Add custom MicroPython documentation links
  - Optimize stub loading performance
  
- **MicroPython-Specific Features**
  - Code snippets for common MicroPython patterns
  - Device pin mapping helpers
  - Serial monitor integration (future)

## Technical Architecture (Current)

### LSP Server Setup (✅ PRODUCTION)
**Current Implementation**: WebSocket Bridge to Pyright Server

**Architecture**:
```
Browser (CodeMirror) 
  ↕ WebSocket (ws://localhost:9011/lsp)
pyright-lsp-bridge Server (Node.js/Python)
  ↕ stdio
Pyright LSP Server v1.1.407 (Node.js)
```

**Components**:
- ✅ `jesse-ai/python-language-server` git submodule
- ✅ VSCode tasks: "Start LSP Bridge" (port 9011), "Start HTTP Server" (port 8888)
- ✅ WebSocketTransport class in `src/lsp/websocket-transport.js`
- ✅ SimpleLSPClient handling LSP protocol

### File Structure (Current)

```
mp_codemirror/
├── src/
│   ├── index.html                 # ✅ Main HTML with LSP integration
│   ├── app.js                     # ✅ Main app with Pyright connection
│   ├── styles.css                 # ✅ Updated styles
│   └── lsp/
│       ├── client.js             # ✅ LSP client setup
│       ├── websocket-transport.js # ✅ WebSocket transport
│       ├── diagnostics.js        # ✅ Diagnostics provider
│       ├── completion.js         # 📋 Completion provider (Sprint 10)
│       ├── hover.js              # 📋 Hover provider (Sprint 11)
│       └── utils.js              # ✅ LSP utilities
├── tests/
│   ├── test_lsp_diagnostics.py   # ✅ 8 comprehensive tests
│   ├── test_lsp_completion.py    # 📋 Completion tests (Sprint 10)
│   └── test_lsp_hover.py         # 📋 Hover tests (Sprint 11)
├── jesse-ai/
│   └── python-language-server/   # ✅ Git submodule LSP bridge
├── typings/
│   └── micropython-stdlib-stubs/ # ✅ MicroPython type stubs
└── docs/
    ├── README.md                 # ✅ Setup and usage guide
    ├── TECHNICAL.md              # ✅ Technical documentation
    └── SPRINT3_SUMMARY.md        # ✅ Latest sprint summary
```

## Testing Strategy (Current)

### Automated Tests (✅ PRODUCTION)
- **8 comprehensive Playwright tests** (100% passing)
- **Test execution time**: ~10-15 seconds total
- **Coverage**: Diagnostics display, WebSocket connection, error handling
- **Real Pyright integration**: Tests use actual LSP server

### Test-Driven Development Workflow (✅ ESTABLISHED)
1. Write Playwright test for new feature
2. Run test (should fail initially)
3. Implement feature incrementally
4. Verify existing tests still pass
5. Run new test (should pass)
6. Refactor and optimize
7. Document feature

## Success Criteria Updates

### Core LSP Integration (✅ ACHIEVED)
- ✅ Real Pyright LSP server running and connected
- ✅ WebSocket bridge functional and stable
- ✅ Real-time diagnostics with intelligent debouncing
- ✅ Production-ready error handling
- ✅ Fast, reliable test suite
- ✅ MicroPython stubs integrated

### Sprint 10 Success (Autocompletion)
- [x] Typing `.` shows relevant completions
- [x] Built-in function completions work
- [x] MicroPython module completions accurate
- [x] Performance under 200ms response time
- [x] All automated tests pass

### Sprint 11 Success (Hover Tooltips)
- [x] Hover shows type information
- [x] Function signatures display correctly
- [x] Docstrings render with Markdown
- [x] MicroPython documentation appears
- [x] Tooltips behave consistently

### Production-Ready Success (After Sprint 12)
- [ ] All core LSP features implemented
- [ ] Advanced navigation features working
- [ ] Comprehensive test coverage
- [ ] Performance optimized
- [ ] Documentation complete

## Timeline (Updated)

### Completed (✅)
- **Sprint 1-3**: Core LSP diagnostics integration (3 weeks) - DONE
- **Infrastructure**: Real Pyright server, WebSocket transport, comprehensive tests

### Remaining Work (📋)
- **Sprint 10**: Autocompletion (2 weeks) - NEXT
- **Sprint 11**: Hover tooltips (1-2 weeks)
- **Sprint 12**: Advanced LSP features (2-3 weeks)
- **Sprint 13**: MicroPython enhancements (2 weeks)

**Total Remaining**: ~6-8 weeks for full feature completion

## Resources

### Documentation
- [LSP Specification](https://microsoft.github.io/language-server-protocol/)
- [Pyright Documentation](https://github.com/microsoft/pyright)
- [CodeMirror Autocompletion](https://codemirror.net/docs/ref/#autocomplete)
- [MicroPython Documentation](https://docs.micropython.org/)

### Current Dependencies (✅ PRODUCTION)
- Pyright LSP Server v1.1.407
- WebSocket transport via `jesse-ai/python-language-server`
- CodeMirror 6 with `@codemirror/lint`
- MicroPython stdlib stubs
- Playwright testing framework

## Notes

- ✅ Core LSP functionality is production-ready
- ✅ Test-driven development workflow established
- ✅ Real Pyright server integration complete
- 📋 Focus now shifts to user-facing features (completion, hover)
- 📋 All future work builds on solid foundation
- 📋 MicroPython optimization comes after core LSP features
