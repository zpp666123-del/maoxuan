#!/usr/bin/env python3
"""Generate deterministic SHA-256 and JSON manifests for the development kit."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_NAMES = {
    "MANIFEST.sha256",
    "package-manifest.json",
    "PACKAGE_VALIDATION_REPORT.md",
    "uvicorn.err.log",
    "uvicorn.out.log",
}
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", ".git", ".venv", ".local", "generated", "node_modules"}


def included_files() -> list[Path]:
    result = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if path.name in EXCLUDED_NAMES or any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        result.append(path)
    return sorted(result, key=lambda item: item.relative_to(ROOT).as_posix())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    files = included_files()
    entries = []
    lines = []
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        checksum = sha256(path)
        size = path.stat().st_size
        lines.append(f"{checksum}  {relative}")
        entries.append({"path": relative, "sha256": checksum, "bytes": size})

    (ROOT / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "package": ROOT.name,
        "version": "1.1.0",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "fileCount": len(entries),
        "totalBytes": sum(item["bytes"] for item in entries),
        "files": entries,
    }
    (ROOT / "package-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {len(entries)} entries")


if __name__ == "__main__":
    main()
