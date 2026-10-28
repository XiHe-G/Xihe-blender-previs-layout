"""Locate and run Blender/ffmpeg without requiring MCP or an add-on."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def _first(candidates: list[str | Path]) -> Path | None:
    for candidate in candidates:
        if not candidate:
            continue
        resolved = shutil.which(str(candidate)) or str(candidate)
        path = Path(resolved)
        if path.is_file():
            return path.resolve()
    return None


def find_blender(explicit: str | Path | None = None) -> Path:
    found = _first([
        explicit or "",
        os.environ.get("BLENDER_EXECUTABLE", ""),
        "blender",
        "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe",
        "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe",
    ])
    if found is None:
        raise FileNotFoundError("Blender executable not found; pass --blender or set BLENDER_EXECUTABLE")
    return found


def find_ffmpeg(explicit: str | Path | None = None) -> Path:
    found = _first([explicit or "", os.environ.get("FFMPEG_EXECUTABLE", ""),
                    "C:/Program Files/EVCapture/ffmpeg.exe", "ffmpeg"])
    if found is None:
        raise FileNotFoundError("ffmpeg executable not found; pass --ffmpeg")
    return found


def find_ffprobe(ffmpeg: str | Path) -> Path:
    sibling = Path(ffmpeg).with_name("ffprobe.exe" if os.name == "nt" else "ffprobe")
    found = _first([sibling, "ffprobe"])
    if found is None:
        raise FileNotFoundError("ffprobe executable not found beside ffmpeg")
    return found


def run_blender(blender: str | Path, script: str | Path, plan: str | Path, output: str | Path,
                mode: str, render: bool, existing_blend: str | Path | None = None) -> subprocess.CompletedProcess:
    command = [str(blender), "--background"]
    if existing_blend and Path(existing_blend).is_file():
        command.append(str(Path(existing_blend).resolve()))
    command.extend(["--python", str(Path(script).resolve()), "--", "--plan", str(Path(plan).resolve()),
                    "--output", str(Path(output).resolve()), "--mode", mode])
    if render:
        command.append("--render")
    result = subprocess.run(command, check=True, text=True, encoding="utf-8", errors="replace",
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # Blender can return exit code 0 after a Python traceback in some bundled
    # builds. Treat the traceback marker as a failed build so packaging never
    # consumes an empty or partial frame directory.
    if "Traceback (most recent call last):" in result.stdout:
        raise RuntimeError("Blender Python build failed:\n" + result.stdout)
    return result
