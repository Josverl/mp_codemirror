# Frank — History

## Project Context
- **Project:** mp_codemirror — CodeMirror 6 editor with Pyright LSP in a Web Worker for MicroPython
- **Stack:** HTML5, ES6+ JavaScript, CodeMirror 6 (CDN/esm.sh), Pyright Web Worker, webpack, pytest + Playwright
- **User:** Jos
- **Audience:** Tool developers who build products with CodeMirror, targeting MicroPython users

## Learnings

### 2026-04-21: SHOWCASE.md created
- Created `SHOWCASE.md` — comprehensive showcase document covering demo walkthrough, video script, micropython-stubs rationale, architecture overview, implementation path, limitations, and future improvements.
- Key source files for understanding features: `README.md`, `QUICKSTART.md`, `src/index.html`, `src/app.js`, `assets/stubs-manifest.json`, `webpack.config.cjs`.
- Board stubs available: ESP32 (bundled), RP2040, STM32 — all from micropython-*-stubs v1.28.0.
- Example files: `blink_led.py`, `temperature_sensor.py`, `espnow.py`, `rp2_pio.py`.
- Architecture reference for docs/architecture.md (Virgil's deliverable) is mentioned but not depended on.
