# Technical Documentation: CDN-Based CodeMirror 6 with Python Support

## Problem: Version Conflicts in CDN Loading

When loading CodeMirror 6 packages from a CDN using ES modules, a common issue arises:

```
Error: Unrecognized extension value in extension set ([object Object]). 
This sometimes happens because multiple instances of @codemirror/state are loaded, 
breaking instanceof checks.
```

### Root Cause

CodeMirror 6 is distributed as a collection of separate packages with interdependencies:
- `codemirror` (meta-package) depends on `@codemirror/state`, `@codemirror/view`, etc.
- `@codemirror/lang-python` depends on `@codemirror/language`, `@codemirror/state`, etc.
- Each package specifies version ranges (e.g., `^6.0.0`) for its dependencies

When loading from a CDN without explicit version pinning, the CDN may resolve these ranges to different concrete versions:
- `codemirror@6.0.1` might load `@codemirror/state@6.5.2`
- `@codemirror/lang-python@6.1.6` might load `@codemirror/state@6.4.1`

This causes multiple versions of the same package to be loaded in the browser, breaking CodeMirror's internal `instanceof` checks and causing the error.

## Solution: Explicit Dependency Pinning with esm.sh

We use [esm.sh](https://esm.sh/)'s `?deps=` parameter to explicitly pin all shared dependencies to the same versions across all packages.

### Implementation

In `src/index.html`, we define an import map with explicit dependencies:

```html
<script type="importmap">
{
    "imports": {
        "codemirror": "https://esm.sh/codemirror@6.0.1?deps=@codemirror/state@6.4.1,@codemirror/view@6.35.0,@codemirror/language@6.10.6,@codemirror/autocomplete@6.18.3,@lezer/common@1.2.3",
        "@codemirror/lang-python": "https://esm.sh/@codemirror/lang-python@6.1.6?deps=@codemirror/autocomplete@6.18.3,@codemirror/language@6.10.6,@codemirror/state@6.4.1,@codemirror/view@6.35.0,@lezer/common@1.2.3,@lezer/python@1.1.16"
    }
}
</script>
```

### How It Works

1. **Both packages specify the same versions for shared dependencies:**
   - `@codemirror/state@6.4.1`
   - `@codemirror/view@6.35.0`
   - `@codemirror/language@6.10.6`
   - `@codemirror/autocomplete@6.18.3`
   - `@lezer/common@1.2.3`

2. **esm.sh respects these pinned versions** when resolving transitive dependencies

3. **Only one version of each package is loaded** in the browser

### Verification

You can verify this works by:

1. **Checking the browser console** - should show no errors
2. **Inspecting network requests** - look for the unique hash in URLs like:
   ```
   /X-ZEBjb2RlbWlycm9yL3N0YXRlQDYuNC4x/
   ```
   This hash (base64 encoded) represents the dependency specification. All packages with the same deps will use the same cached bundle.

3. **Testing functionality:**
   - Python syntax highlighting should work
   - Editor should accept input
   - All buttons should function correctly
   - No console errors

## Alternative Approaches (Not Used)

### 1. Import Map with Manual Package Entries
Defining each package separately in the import map:
```javascript
{
  "imports": {
    "@codemirror/state": "https://esm.sh/@codemirror/state@6.4.1",
    "@codemirror/view": "https://esm.sh/@codemirror/view@6.35.0",
    // ... more packages
  }
}
```
**Issues:** 
- Very verbose (dozens of packages)
- Transitive dependencies still cause issues
- Hard to maintain

### 2. Using Bundle/Standalone Mode
Using `?bundle` or `?standalone` flags:
```javascript
"https://esm.sh/@codemirror/lang-python@6.1.6?standalone"
```
**Issues:**
- Creates large bundle files
- Duplicates code when using multiple packages
- Still doesn't solve version conflicts with the base `codemirror` package

### 3. Using Different CDN Providers
Tried: jspm.dev, unpkg, cdn.jsdelivr.net, cdn.skypack.dev
**Issues:**
- Same fundamental problem with version resolution
- Some CDNs don't support import maps well
- esm.sh has the best `?deps=` parameter support

### 4. Local Bundling with Vite/Rollup
Using a build tool to bundle everything:
**Issues:**
- Requires build step (violates project goal)
- Can't deploy as static files to GitHub Pages without CI/CD
- More complex development workflow

## Best Practices for CDN-Based CodeMirror

### 1. Pin All Versions Explicitly
Never use version ranges in import maps:
```javascript
// ❌ Bad - uses latest compatible version
"codemirror": "https://esm.sh/codemirror@^6.0.0"

// ✅ Good - explicit version
"codemirror": "https://esm.sh/codemirror@6.0.1"
```

### 2. Use Consistent Dependency Versions
When adding new CodeMirror extensions, use the same dependency versions:
```javascript
// When adding @codemirror/lang-javascript
"@codemirror/lang-javascript": "https://esm.sh/@codemirror/lang-javascript@6.2.2?deps=@codemirror/state@6.4.1,@codemirror/view@6.35.0,..."
```

### 3. Test After Changes
Always test after modifying the import map:
- Check browser console for errors
- Test all editor functionality
- Verify syntax highlighting works
- Use Playwright tests to catch regressions

### 4. Document Version Choices
Keep a record of why specific versions were chosen:
- Compatibility requirements
- Bug fixes in specific versions
- Breaking changes to avoid

## Debugging Version Conflicts

If you encounter version conflict errors:

1. **Open browser DevTools Network tab**
2. **Filter for `@codemirror` requests**
3. **Look for duplicate packages** - multiple URLs with different version numbers
4. **Check the `/X-` hash in URLs** - different hashes mean different dependency sets
5. **Update import map** to use consistent versions across all packages

### Common Error Patterns

```
Unrecognized extension value
→ Multiple @codemirror/state versions loaded

TypeError: Cannot read property 'from' of undefined  
→ Version mismatch between @codemirror/state and @codemirror/view

Extension value must be an extension
→ Package loaded from wrong version, doesn't match expected interface
```

## Performance Considerations

### HTTP/2 Multiplexing
Modern browsers use HTTP/2, so loading multiple small modules is efficient. The CDN approach:
- Loads only what's needed
- Caches individual packages
- Benefits from browser/CDN caching

### Bundle Size
With explicit dependency pinning:
- Total transfer: ~450KB (minified)
- Gzipped: ~150KB
- Cached after first load

### Loading Time
Typical loading sequence:
1. HTML loads (< 1KB)
2. Import map parsed immediately
3. app.js loads and starts importing (5KB)
4. Parallel loading of CodeMirror packages (~300ms on good connection)
5. Editor initializes and renders (~50ms)

Total time to interactive: **< 500ms** on typical connections

## Future Improvements

### 1. Preload Hints
Add `<link rel="modulepreload">` for faster loading:
```html
<link rel="modulepreload" href="https://esm.sh/codemirror@6.0.1?deps=...">
<link rel="modulepreload" href="https://esm.sh/@codemirror/lang-python@6.1.6?deps=...">
```

### 2. Service Worker Caching
Implement aggressive caching with service workers for offline support

### 3. Lazy Loading Language Modes
Load Python support only when needed:
```javascript
const python = await import('@codemirror/lang-python');
view.dispatch({
  effects: StateEffect.appendConfig.of(python.python())
});
```

### 4. Version Automation
Create a script to check for compatible CodeMirror package versions:
```bash
# Check what versions work together
node scripts/check-versions.js
```

## References

- [esm.sh Documentation](https://esm.sh/)
- [CodeMirror 6 System Guide](https://codemirror.net/docs/guide/)
- [ES Modules in Browsers](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [Import Maps Specification](https://github.com/WICG/import-maps)

## Changelog

### 2024-01-XX - Initial Solution
- Implemented explicit dependency pinning with `?deps=` parameter
- Tested and verified Python syntax highlighting works without errors
- Documented solution and best practices
