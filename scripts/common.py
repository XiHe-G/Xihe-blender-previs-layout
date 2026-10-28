"""Small shared helpers for the Blender Previs Layout V1 runtime."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


VERSION = (Path(__file__).resolve().parents[1] / "VERSION").read_text(encoding="utf-8").strip()
# Scene/manifest V1 tags describe the unchanged runtime contract, not the release.
LEGACY_COMPAT_VERSION = "1.0"
BUILD_MODES = {
    "FULL_BUILD",
    "SHOT_BUILD",
    "CAMERA_ONLY",
    "BLOCKING_ONLY",
    "MOTION_ONLY",
    "OVERRIDE_PATCH",
    "RENDER_ONLY",
}


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(path: str | Path, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def slug(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in value.strip())
    return cleaned.strip("-") or "previs"
