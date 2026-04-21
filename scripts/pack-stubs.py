#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Pack MicroPython board stubs into zip files for browser use.

For each board defined below:
  1. Install stubs via `uv pip install micropython-{board}-stubs --target ./tmp`
  2. Zip the .pyi files and packages (skip dist-info metadata)
  3. Write to assets/stubs-{board}.zip
  4. Generate assets/stubs-manifest.json

Usage: uv run scripts/pack-stubs.py [board...]
  No args -> pack all boards.  Pass board IDs to pack specific ones.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
TMP = ROOT / "tmp_stubs"


@dataclass
class Board:
    id: str
    name: str
    package: str
    description: str
    bundled: bool = False
    file: str | None = None
    size: int = 0


# Boards that have installable stub packages
BOARDS: list[Board] = [
    Board(
        id="esp32",
        name="esp32 ESP32_GENERIC",
        package="micropython-esp32-stubs",
        description="ESP32 with WiFi, BLE, machine, esp32 modules",
        bundled=True,
    ),
    Board(
        id="rp2",
        name="rp2 Pico_W (RP2040)",
        package="micropython-rp2-stubs",
        description="RP2040 with PIO, machine, rp2 modules",
    ),
    Board(
        id="stm32",
        name="stm32 PYBV11",
        package="micropython-stm32-stubs",
        description="STM32 with machine, pyb modules",
    ),
]

# Virtual boards (no stub package, included in manifest only)
VIRTUAL_BOARDS: list[Board] = [
    Board(
        id="cpython",
        name="Just CPython (no stubs)",
        package="",
        description="Standard CPython only — no MicroPython stubs loaded",
    ),
]

BOARD_MAP = {b.id: b for b in BOARDS}


def zip_directory(source_dir: Path, out_path: Path) -> int:
    """Zip a directory, skipping .dist-info folders. Returns size in bytes."""
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for entry in sorted(source_dir.iterdir()):
            if entry.name.endswith(".dist-info"):
                continue
            if entry.is_dir():
                for root_dir, _dirs, files in os.walk(entry):
                    for f in files:
                        full = Path(root_dir) / f
                        arcname = full.relative_to(source_dir)
                        zf.write(full, arcname)
            else:
                zf.write(entry, entry.name)
    return out_path.stat().st_size


def pack_board(board: Board) -> Board:
    """Install stubs and pack them into a zip. Returns updated board."""
    target = TMP / board.id

    # Clean and install
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    print(f"  Installing {board.package}...")
    subprocess.run(
        ["uv", "pip", "install", board.package, "--target", str(target), "--quiet"],
        check=True,
        capture_output=True,
        text=True,
    )

    # Zip
    out_path = ASSETS / f"stubs-{board.id}.zip"
    size = zip_directory(target, out_path)
    print(f"  → assets/stubs-{board.id}.zip  ({size / 1024:.0f} KB)")

    board.file = f"stubs-{board.id}.zip"
    board.size = size
    return board


def main() -> None:
    requested_ids = sys.argv[1:]
    boards = (
        [b for b in BOARDS if b.id in requested_ids] if requested_ids else list(BOARDS)
    )

    if requested_ids and not boards:
        available = ", ".join(b.id for b in BOARDS)
        print(f"No matching boards. Available: {available}", file=sys.stderr)
        sys.exit(1)

    ASSETS.mkdir(parents=True, exist_ok=True)

    print(f"Packing stubs for {len(boards)} board(s)...")
    results: list[Board] = []
    for board in boards:
        print(f"\n[{board.id}] {board.name}")
        results.append(pack_board(board))

    # Add virtual boards to the manifest
    for vb in VIRTUAL_BOARDS:
        results.append(vb)

    # Generate manifest
    default_id = next((b.id for b in BOARDS if b.bundled), boards[0].id)
    manifest = {
        "version": "1.0",
        "default": default_id,
        "boards": [
            {
                "id": b.id,
                "name": b.name,
                "file": b.file,
                "size": b.size,
                "description": b.description,
                "bundled": b.bundled,
            }
            for b in results
        ],
    }

    manifest_path = ASSETS / "stubs-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nManifest → assets/stubs-manifest.json")

    # Clean up
    if TMP.exists():
        shutil.rmtree(TMP)
    print("Done.")


if __name__ == "__main__":
    main()
