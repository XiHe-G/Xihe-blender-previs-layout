"""Revision receipts shared by existing-scene production tools."""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_path(base, value):
    value = Path(value)
    return value.resolve() if value.is_absolute() else (Path(base) / value).resolve()


def png_size(path):
    with Path(path).open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Not a PNG: {path}")
    return list(struct.unpack(">II", header[16:24]))


def render_fingerprint(job, paths):
    digest = hashlib.sha256(json.dumps(job, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    for path in sorted(set(Path(p).resolve() for p in paths), key=str):
        digest.update(str(path).encode("utf-8"))
        digest.update(sha256(path).encode("ascii"))
    return digest.hexdigest()


def reusable_frame(path, fingerprint, dimensions):
    path = Path(path)
    try:
        receipt = read_json(path.with_suffix(".receipt.json"))
        return (receipt["fingerprint"] == fingerprint
                and receipt["dimensions"] == dimensions
                and png_size(path) == dimensions
                and receipt["sha256"] == sha256(path))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def compare_files(files, previous):
    old = {str(Path(row["path"]).resolve()).casefold(): row.get("sha256")
           for row in previous.get("files", [])}
    comparisons = []
    for row in files:
        before = old.get(str(Path(row["path"]).resolve()).casefold())
        comparisons.append({"path": row["path"], "status":
                            "not_in_previous" if before is None else
                            "match" if before == row.get("sha256") else "mismatch",
                            "previous_sha256": before, "current_sha256": row.get("sha256")})
    return comparisons
