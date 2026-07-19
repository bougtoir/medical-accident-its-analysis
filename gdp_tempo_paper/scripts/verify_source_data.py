"""Verify frozen source-data checksums and declared row counts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from data_sources import SOURCE_DATA


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    manifest_path = SOURCE_DATA / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    for entry in manifest["files"]:
        path = SOURCE_DATA / entry["path"]
        if not path.exists():
            failures.append(f"missing: {path}")
            continue
        actual_hash = sha256(path)
        if actual_hash != entry["sha256"]:
            failures.append(f"checksum mismatch: {path}")
        actual_rows = len(pd.read_csv(path))
        if actual_rows != entry["rows"]:
            failures.append(
                f"row-count mismatch: {path} ({actual_rows} != {entry['rows']})"
            )
        print(f"verified {entry['path']}: {actual_rows} rows, sha256={actual_hash}")
    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
