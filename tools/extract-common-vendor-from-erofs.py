#!/usr/bin/env python3

from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd()
MANIFEST = ROOT / "device/samsung/sm8250-common/proprietary-files.txt"
IMAGE = ROOT / "work/lineage-vendor/vendor.img"
DEST = ROOT / "vendor/samsung/sm8250-common/proprietary"

entries = []

for raw in MANIFEST.read_text().splitlines():
    line = raw.strip()

    if not line or line.startswith("#"):
        continue

    # Remove hash fields and directives
    path = line.split("|", 1)[0]
    directive = ""

    if ";" in path:
        path, directive = path.split(";", 1)

    path = path.strip()

    if not path.startswith("vendor/"):
        continue

    # SYMLINK entries are handled separately
    if directive.startswith("SYMLINK="):
        continue

    entries.append(path)

print(f"Vendor entries: {len(entries)}")
print(f"Source: {IMAGE}")
print(f"Destination: {DEST}")
print()

if not IMAGE.exists():
    print("ERROR: vendor.img not found")
    sys.exit(1)

DEST.mkdir(parents=True, exist_ok=True)

failed = []

for i, path in enumerate(entries, 1):
    internal = path[len("vendor/"):]
    output = DEST / path
    output.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "dump.erofs",
            "--cat",
            f"--path={internal}",
            str(IMAGE),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode != 0 or not result.stdout:
        failed.append((path, result.stderr.decode(errors="replace").strip()))
        print(f"[{i}/{len(entries)}] FAILED  {path}")
        continue

    output.write_bytes(result.stdout)
    print(f"[{i}/{len(entries)}] extracted {path}")

print()
print("=" * 60)
print(f"Extracted : {len(entries) - len(failed)}/{len(entries)}")
print(f"Failed    : {len(failed)}")

if failed:
    print()
    print("FAILED FILES:")
    for path, error in failed:
        print(f"- {path}")
        if error:
            print(f"  {error}")
    sys.exit(1)

print()
print("SUCCESS")
