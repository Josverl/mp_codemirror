# Tess — History

## Project Context
- **Project:** mp_codemirror — CodeMirror 6 editor with Pyright LSP in a Web Worker for MicroPython
- **Stack:** HTML5, ES6+ JavaScript, CodeMirror 6 (CDN/esm.sh), Pyright Web Worker, webpack, pytest + Playwright
- **User:** Jos
- **Audience:** Tool developers who build products with CodeMirror, targeting MicroPython users

## Learnings

### 2026-04-21: Documentation Cleanup & Review Fixes
- Archived historical artifacts to `.ai_history/`: PYRIGHT_LSP_PLAN.md, CDN_TEST_REPORT.md, JESSE_AI_WINDOWS_ISSUE.md
- README.md: CDN version was wrong (6.0.1 vs actual 6.0.2), roadmap was stale (Phase 2/3 marked incomplete when done), `rp2_pio.py` missing from project structure, testing prereqs used pip instead of uv
- CONTRIBUTING.md: Was pointing to port 8000 and test.html (neither exist), needed full setup rewrite with uv sync + just build + proper test commands
- server/README.md: Had PowerShell code blocks and Windows paths, needed dev-only disclaimer at top, cleanup section referenced nonexistent dirs
- tests/README.md: Had "start servers" prereq that's wrong (fixtures auto-start), Windows commands (netstat/taskkill)
- src/examples/README.md: UI description didn't match actual dropdown+Load button pattern
- PYRIGHT_LSP_PLAN.md and SPRINT_2: Updated checkboxes for completed Sprint 10 (autocompletion), Sprint 11 (hover), and Sprint 2 tasks
- Key: Always check index.html importmap for actual CDN versions before documenting them
