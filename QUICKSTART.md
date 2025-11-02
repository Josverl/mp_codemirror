# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Initialize the Project

```bash
# Clone and setup
git clone <repository-url>
cd mp_codemirror

# Initialize LSP bridge submodule
git submodule update --init --recursive
cd server/pyright-lsp-bridge
npm install
cd ../..
```

### Step 2: Start the Servers

**Option A: Using VSCode Tasks (Recommended)**

1. Open the project in VSCode
2. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
3. Type "Tasks: Run Task"
4. Select **"Start All Servers"**
5. Both servers start automatically! 🎉

**Option B: Manual Start**

Terminal 1 - LSP Bridge:
```bash
cd server/pyright-lsp-bridge
npm start
```

Terminal 2 - HTTP Server:
```bash
python -m http.server 8888
```

### Step 3: Open in Browser

Navigate to: `http://localhost:8888/src/`

Start coding with real-time LSP diagnostics! 🐍✨

---

## 📋 VSCode Tasks

### Available Tasks

- **Start All Servers** - Starts both LSP and HTTP server
- **Start LSP Bridge** - Only starts the Pyright LSP bridge (port 9011)
- **Start HTTP Server** - Only starts the Python HTTP server (port 8888)

### Task Shortcuts

```
Ctrl+Shift+P → Tasks: Run Task → Select task
```

Or configure a keyboard shortcut in VSCode:
```json
// .vscode/keybindings.json
[
    {
        "key": "ctrl+shift+s",
        "command": "workbench.action.tasks.runTask",
        "args": "Start All Servers"
    }
]
```

---

## 📋 Quick Commands

### Local Development

**With VSCode:**
```bash
# Use tasks (Ctrl+Shift+P → Tasks: Run Task → Start All Servers)
```

**Manual:**
```bash
# LSP Bridge
cd server/pyright-lsp-bridge
npm start

# HTTP Server (separate terminal)
python -m http.server 8888
```

**Alternative HTTP Servers:**
```bash
# Node.js
npx serve -p 8888

# PHP
php -S localhost:8888
```

### Testing

```bash
# Run Playwright tests
pytest tests/ -v

# Run with browser visible
pytest tests/ --headed

# Run specific test
pytest tests/test_editor.py::test_page_loads -v
```

### Git Commands

```bash
# Create new feature
git checkout -b feature/my-feature

# Add and commit changes
git add .
git commit -m "feat: add my feature"

# Push to GitHub
git push origin feature/my-feature
```

---

## ⌨️ Editor Keyboard Shortcuts

### Windows/Linux

| Action | Shortcut |
|--------|----------|
| Find | `Ctrl+F` |
| Replace | `Ctrl+H` |
| Undo | `Ctrl+Z` |
| Redo | `Ctrl+Y` |
| Comment | `Ctrl+/` |
| Indent | `Tab` |
| Dedent | `Shift+Tab` |
| Fold Code | `Ctrl+Shift+[` |
| Unfold Code | `Ctrl+Shift+]` |
| Select All | `Ctrl+A` |
| Go to Line | `Ctrl+G` |

### macOS

| Action | Shortcut |
|--------|----------|
| Find | `Cmd+F` |
| Replace | `Cmd+Alt+F` |
| Undo | `Cmd+Z` |
| Redo | `Cmd+Shift+Z` |
| Comment | `Cmd+/` |
| Indent | `Tab` |
| Dedent | `Shift+Tab` |
| Fold Code | `Cmd+Alt+[` |
| Unfold Code | `Cmd+Alt+]` |
| Select All | `Cmd+A` |
| Go to Line | `Cmd+G` |

---

## 🎨 Customization

### Change Editor Font

Edit `app.js`:

```javascript
const darkTheme = EditorView.theme({
    ".cm-content": {
        fontFamily: "'Your Font', monospace",  // Change this
        fontSize: "16px"  // Change size
    }
});
```

### Change Theme Colors

Edit the theme objects in `app.js`:

```javascript
const darkTheme = EditorView.theme({
    "&": {
        backgroundColor: "#your-color",
        color: "#your-text-color"
    }
});
```

### Add More Python Code Samples

Edit `app.js`, modify the `sampleCode` constant:

```javascript
const sampleCode = `# Your custom sample here
print("Hello, World!")
`;
```

---

## 🐛 Common Issues

### Editor doesn't load

**Problem:** "Failed to fetch" errors

**Solution:** Make sure you're using a web server, not opening `file://` directly

```bash
# Start a server first!
python -m http.server 8000
```

### Import map not working

**Problem:** Module resolution errors

**Solution:** 
1. Check browser version (need Chrome 89+, Firefox 89+, Safari 15+)
2. Clear browser cache
3. Try incognito/private mode

### Syntax highlighting not working

**Problem:** Code shows as plain text

**Solution:**
1. Wait a moment for CDN to load
2. Check browser console for errors
3. Verify internet connection (CDN required)

---

## 📦 Deployment to GitHub Pages

### Automatic Deployment (Recommended)

1. Push to `main` branch
2. GitHub Actions will automatically deploy
3. Wait ~2 minutes
4. Visit `https://YOUR_USERNAME.github.io/REPO_NAME/`

### Manual Deployment

1. Go to repository Settings
2. Navigate to Pages section
3. Select `main` branch and `/src` folder
4. Click Save
5. Wait for deployment
6. Visit the provided URL

---

## 🧪 Testing Checklist

Before committing changes:

- [ ] LSP bridge starts without errors
- [ ] HTTP server serves files
- [ ] Editor loads at http://localhost:8888/src/
- [ ] Real-time diagnostics working
- [ ] Syntax highlighting works
- [ ] All buttons functional
- [ ] Theme toggle works
- [ ] Console has no errors
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Mobile view works

---

## 📚 Resources

### CodeMirror Documentation
- [Main Docs](https://codemirror.net/6/)
- [Examples](https://codemirror.net/examples/)
- [API Reference](https://codemirror.net/docs/ref/)

### Development
- [ES Modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [Import Maps](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/script/type/importmap)

### Python
- [MicroPython](https://micropython.org/)
- [Python Docs](https://docs.python.org/3/)

---

## 💡 Tips

### Performance

- Editor handles large files (tested up to 10,000 lines)
- Syntax highlighting is lazy-loaded
- CDN modules are cached by browser

### Accessibility

- All buttons have ARIA labels
- Keyboard navigation supported
- Screen reader compatible

### Browser DevTools

```javascript
// Access editor in console (for debugging)
import('/app.js').then(module => {
    console.log(module.view.state.doc.toString());
});
```

---

## 🤝 Get Help

- Open an [Issue](../../issues)
- Check [Discussions](../../discussions)
- Read [Contributing Guide](CONTRIBUTING.md)

---

**Happy Coding! 🐍✨**
