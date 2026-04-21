#!/usr/bin/env node
/**
 * Pack MicroPython board stubs into zip files for browser use.
 *
 * For each board defined below:
 *   1. Install stubs via `uv pip install micropython-{board}-stubs --target ./tmp`
 *   2. Zip the .pyi files and packages (skip dist-info metadata)
 *   3. Write to assets/stubs-{board}.zip
 *   4. Generate assets/stubs-manifest.json
 *
 * Usage: node scripts/pack-stubs.mjs [board...]
 *   No args → pack all boards.  Pass board IDs to pack specific ones.
 */

import { execSync } from "child_process";
import * as fs from "fs";
import * as path from "path";
import archiver from "archiver";

const BOARDS = [
    {
        id: "esp32",
        name: "ESP32 (Generic)",
        package: "micropython-esp32-stubs",
        description: "ESP32 with WiFi, BLE, machine, esp32 modules",
        bundled: true,
    },
    {
        id: "rp2",
        name: "Raspberry Pi Pico (RP2040)",
        package: "micropython-rp2-stubs",
        description: "RP2040 with PIO, machine, rp2 modules",
        bundled: false,
    },
    {
        id: "stm32",
        name: "STM32 (Generic)",
        package: "micropython-stm32-stubs",
        description: "STM32 with machine, pyb modules",
        bundled: false,
    },
];

const ROOT = path.resolve(import.meta.dirname, "..");
const ASSETS = path.join(ROOT, "assets");
const TMP = path.join(ROOT, "tmp_stubs");

function zipDirectory(sourceDir, outPath) {
    return new Promise((resolve, reject) => {
        const output = fs.createWriteStream(outPath);
        const archive = archiver("zip", { zlib: { level: 9 } });

        output.on("close", () => resolve(archive.pointer()));
        archive.on("error", reject);

        archive.pipe(output);

        // Walk the directory and add .pyi files + package dirs (skip dist-info)
        const entries = fs.readdirSync(sourceDir, { withFileTypes: true });
        for (const entry of entries) {
            if (entry.name.endsWith(".dist-info")) continue;
            const full = path.join(sourceDir, entry.name);
            if (entry.isDirectory()) {
                archive.directory(full, entry.name);
            } else {
                archive.file(full, { name: entry.name });
            }
        }

        archive.finalize();
    });
}

async function packBoard(board) {
    const target = path.join(TMP, board.id);

    // Clean and install
    if (fs.existsSync(target)) {
        fs.rmSync(target, { recursive: true });
    }
    fs.mkdirSync(target, { recursive: true });

    console.log(`  Installing ${board.package}...`);
    execSync(`uv pip install ${board.package} --target "${target}" --quiet`, {
        stdio: ["pipe", "pipe", "inherit"],
    });

    // Zip
    const outPath = path.join(ASSETS, `stubs-${board.id}.zip`);
    const size = await zipDirectory(target, outPath);
    console.log(
        `  → assets/stubs-${board.id}.zip  (${(size / 1024).toFixed(0)} KB)`
    );

    return { ...board, size, file: `stubs-${board.id}.zip` };
}

async function main() {
    const requestedIds = process.argv.slice(2);
    const boards =
        requestedIds.length > 0
            ? BOARDS.filter((b) => requestedIds.includes(b.id))
            : BOARDS;

    if (boards.length === 0) {
        console.error(
            `No matching boards. Available: ${BOARDS.map((b) => b.id).join(", ")}`
        );
        process.exit(1);
    }

    fs.mkdirSync(ASSETS, { recursive: true });

    console.log(`Packing stubs for ${boards.length} board(s)...`);
    const results = [];
    for (const board of boards) {
        console.log(`\n[${board.id}] ${board.name}`);
        results.push(await packBoard(board));
    }

    // Generate manifest
    const manifest = {
        version: "1.0",
        default: BOARDS.find((b) => b.bundled)?.id || boards[0].id,
        boards: results.map((r) => ({
            id: r.id,
            name: r.name,
            file: r.file,
            size: r.size,
            description: r.description,
            bundled: r.bundled || false,
        })),
    };

    const manifestPath = path.join(ASSETS, "stubs-manifest.json");
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
    console.log(`\nManifest → assets/stubs-manifest.json`);

    // Clean up
    if (fs.existsSync(TMP)) {
        fs.rmSync(TMP, { recursive: true });
    }
    console.log("Done.");
}

main().catch((err) => {
    console.error(err);
    process.exit(1);
});
