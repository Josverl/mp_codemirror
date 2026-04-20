# CDN Error Test Report

## Test Date
2026-04-20 (re-tested after CDN configuration update)

## Test Method
Playwright MCP Server - Headless Chromium Browser

## Summary
**Status: CDN Resources Load Successfully ✅**

After updating the CDN configuration and upgrading to current CodeMirror package versions,
all resources from `esm.sh` load without errors and the editor initialises correctly.

## Fix Applied

The root cause was a **version mismatch** in the import map. `codemirror@6.0.1` (the umbrella
package) imported `showDialog` from `@codemirror/view`, which was only added in
`@codemirror/view@6.36.0`. The import map was pinning `@codemirror/view@6.35.0`, causing a
module export error that prevented the editor from initialising.

### Updated versions in `src/index.html`

| Package | Before | After |
|---------|--------|-------|
| `codemirror` | 6.0.1 | 6.0.2 |
| `@codemirror/state` | 6.4.1 | 6.6.0 |
| `@codemirror/view` | 6.35.0 | 6.41.1 |
| `@codemirror/language` | 6.10.6 | 6.12.3 |
| `@codemirror/autocomplete` | 6.18.3 | 6.20.1 |
| `@codemirror/lint` | 6.8.4 | 6.9.5 |
| `@codemirror/lang-python` | 6.1.6 | 6.2.1 |
| `@lezer/common` | 1.2.3 | 1.5.2 |
| `@lezer/python` | 1.1.16 | 1.1.18 |

## Test Results After Fix

### Console errors
- ❌ (resolved) `ERR_BLOCKED_BY_CLIENT` for esm.sh CDN resources
- ❌ (resolved) `showDialog` module export error
- ⚠️ WebSocket connection refused on port 9011 — expected; LSP server not running in CI

### Page functionality
✅ Page HTML, CSS and local JS load (HTTP 200)  
✅ CodeMirror `.cm-editor` element renders  
✅ Python syntax highlighting active  
✅ Line numbers displayed  
✅ Code-folding indicators present  
✅ Example files populate the selector dropdown  
✅ Default example (`blink_led.py`) loads into the editor  

## Screenshot

![Editor working with Python syntax highlighting](https://github.com/user-attachments/assets/77b7f1ba-b8e0-479e-b348-5659578d2767)

## Historical Record — Initial CDN Blocking Issue

Prior to the firewall/configuration update, all CDN requests from esm.sh returned
`ERR_BLOCKED_BY_CLIENT` at the browser level. Those errors are now fully resolved.

Previous failing screenshot (for reference):
![CDN blocked — editor blank](https://github.com/user-attachments/assets/5535363f-1f73-447c-8cf7-679eba8d7b07)
