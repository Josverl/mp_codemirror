# Jesse-AI Python Language Server - Windows Build Issue

## Problem

The prebuilt Windows package (win32-x64.zip) from jesse-ai/python-language-server v1.0.2 has a critical bug:

**Error:**
```
(node:40108) Warning: To load an ES module, set "type": "module" in the package.json or use the .mjs extension.
SyntaxError: Cannot use import statement outside a module
```

## Root Cause

The `bundle.js` file uses ES module syntax (`import/export`) but:
1. No `package.json` with `"type": "module"` is included in the package
2. The bundle was not properly configured for Windows during build

## Attempted Fixes

1. ✗ Added `package.json` with `"type": "module"` - didn't help
2. ✗ Used `--input-type=module` flag - doesn't work for file execution
3. ✗ Switched to exact Node.js v20.11.0 - same error
4. ✗ Tried using bundled Node.js runtime - same error

## Conclusion

The Windows prebuilt package is broken. Options:
1. **Use our Python bridge** (CURRENT - WORKING) ✅
2. Build from source on Windows (complex, requires build tools)
3. Report bug to jesse-ai maintainers
4. Wait for fixed release

## Our Solution (Python Bridge)

Our Python WebSocket bridge (`server/lsp_bridge.py`) works perfectly:
- ✅ Tested and working on Windows
- ✅ Real Pyright diagnostics confirmed
- ✅ Simple Python + websockets dependency
- ✅ Easy to maintain and debug

**Decision: Keep our Python implementation**
