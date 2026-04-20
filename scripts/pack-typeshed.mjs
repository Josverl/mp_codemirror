/**
 * Pack Pyright's typeshed-fallback into a zip file for browser use.
 * 
 * Usage: node scripts/pack-typeshed.mjs
 * Output: assets/typeshed-fallback.zip
 */
import { execSync } from "child_process";
import { existsSync, mkdirSync, statSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const typeshedSrc = resolve(
    root,
    "node_modules/pyright/packages/pyright-internal/typeshed-fallback"
);
const assetsDir = resolve(root, "assets");
const outFile = resolve(assetsDir, "typeshed-fallback.zip");

if (!existsSync(typeshedSrc)) {
    console.error(`Typeshed not found at: ${typeshedSrc}`);
    console.error("Run 'npm install --ignore-scripts' first.");
    process.exit(1);
}

mkdirSync(assetsDir, { recursive: true });

// Use Node's built-in to create zip, or fall back to python
console.log(`Packing typeshed from: ${typeshedSrc}`);
console.log(`Output: ${outFile}`);

try {
    // Try system zip first
    execSync(`cd "${typeshedSrc}" && zip -r -q "${outFile}" stdlib stubs LICENSE`, {
        stdio: "inherit",
    });
} catch {
    // Fall back to Python's zipfile
    console.log("zip not found, using Python...");
    execSync(
        `python3 -c "
import zipfile, os
src = '${typeshedSrc}'
out = '${outFile}'
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root_dir, dirs, files in os.walk(src):
        for f in files:
            full = os.path.join(root_dir, f)
            arcname = os.path.relpath(full, src)
            zf.write(full, arcname)
print(f'Written: {out}')
"`,
        { stdio: "inherit" }
    );
}

const size = statSync(outFile).size;
console.log(`Done: ${(size / 1024 / 1024).toFixed(2)} MB`);
