"""Remove only reproducible frame and Python bytecode caches below a chosen root."""

from __future__ import annotations

import argparse
from pathlib import Path


def _inside(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    resolved.relative_to(root)
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    removed_files = 0
    removed_dirs = 0
    for directory in list(root.rglob("frames")):
        directory = _inside(directory, root)
        if directory.is_symlink() or directory.parent.name != "_work":
            continue
        for file in directory.iterdir():
            file = _inside(file, root)
            if file.is_file() and file.name.startswith("F") and file.suffix.lower() == ".png":
                file.unlink(); removed_files += 1
        if not any(directory.iterdir()):
            directory.rmdir(); removed_dirs += 1
    for directory in sorted(root.rglob("__pycache__"), reverse=True):
        directory = _inside(directory, root)
        if directory.is_symlink():
            continue
        for file in directory.iterdir():
            file = _inside(file, root)
            if file.is_file() and file.suffix.lower() == ".pyc":
                file.unlink(); removed_files += 1
        if not any(directory.iterdir()):
            directory.rmdir(); removed_dirs += 1
    for file in root.rglob("*.blend1"):
        file = _inside(file, root)
        if file.is_file():
            file.unlink(); removed_files += 1
    print(f"Removed {removed_files} generated files from {removed_dirs} cache directories below {root}")


if __name__ == "__main__":
    main()
