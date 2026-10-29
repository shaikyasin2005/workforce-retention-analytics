from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "docs" / "source_manifest.json"

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
}

EXCLUDED_FILES = {
    "source_manifest.json",
    "ground_truth.json",
}


def sha256_file(path):
    """Calculate the SHA-256 checksum of a file."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    records = []

    for path in sorted(PROJECT_ROOT.rglob("*")):
        if not path.is_file():
            continue

        relative_path = path.relative_to(PROJECT_ROOT)

        if any(part in EXCLUDED_DIRS for part in relative_path.parts):
            continue

        if path.name in EXCLUDED_FILES:
            continue

        if path == OUTPUT_PATH:
            continue

        # Avoid including generated datasets, databases, and model binaries.
        if relative_path.parts[0] in {"data", "models"}:
            continue

        records.append({
            "path": relative_path.as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })

    manifest = {
        "manifest_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": PROJECT_ROOT.name,
        "files_included": len(records),
        "excluded": [
            "Virtual environments and Git metadata",
            "Generated data and model artifacts",
            "The manifest itself",
        ],
        "files": records,
    }

    OUTPUT_PATH.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print("SOURCE MANIFEST CREATED")
    print(f"Files recorded: {len(records)}")
    print(f"Output: {OUTPUT_PATH}")
    print("SHA-256 checksums calculated successfully.")


if __name__ == "__main__":
    main()