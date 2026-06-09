#!/usr/bin/env python3
"""Add CC BY-NC 4.0 copyright headers to tracked source files."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "Copyright (c) 2026 paidaxin-12138"

HEADERS = {
    "hash": (
        "# Copyright (c) 2026 paidaxin-12138\n"
        "# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.\n"
        "# https://creativecommons.org/licenses/by-nc/4.0/\n"
    ),
    "slash": (
        "// Copyright (c) 2026 paidaxin-12138\n"
        "// Licensed under CC BY-NC 4.0 — see LICENSE in repository root.\n"
        "// https://creativecommons.org/licenses/by-nc/4.0/\n"
    ),
    "html": (
        "<!-- Copyright (c) 2026 paidaxin-12138 — CC BY-NC 4.0 — see LICENSE -->\n"
    ),
    "md": (
        "<!-- Copyright (c) 2026 paidaxin-12138 — CC BY-NC 4.0 — see LICENSE -->\n\n"
    ),
    "wxml": (
        "<!-- Copyright (c) 2026 paidaxin-12138 — CC BY-NC 4.0 — see LICENSE -->\n"
    ),
    "wxss": (
        "/* Copyright (c) 2026 paidaxin-12138 — CC BY-NC 4.0 — see LICENSE */\n"
    ),
    "css": (
        "/* Copyright (c) 2026 paidaxin-12138 — CC BY-NC 4.0 — see LICENSE */\n"
    ),
    "sql": (
        "-- Copyright (c) 2026 paidaxin-12138\n"
        "-- Licensed under CC BY-NC 4.0 — see LICENSE in repository root.\n"
        "-- https://creativecommons.org/licenses/by-nc/4.0/\n"
    ),
    "txt": (
        "Copyright (c) 2026 paidaxin-12138\n"
        "Licensed under CC BY-NC 4.0 — see LICENSE in repository root.\n"
        "https://creativecommons.org/licenses/by-nc/4.0/\n\n"
    ),
}

EXT_STYLE = {
    ".py": "hash",
    ".sh": "hash",
    ".yaml": "hash",
    ".yml": "hash",
    ".ino": "slash",
    ".cpp": "slash",
    ".h": "slash",
    ".js": "slash",
    ".html": "html",
    ".md": "md",
    ".wxml": "wxml",
    ".wxss": "wxss",
    ".css": "css",
    ".sql": "sql",
    ".scad": "slash",
    ".txt": "txt",
}


def tracked_files() -> list[Path]:
    out = subprocess.check_output(
        ["git", "-c", "core.quotepath=false", "ls-files"],
        cwd=ROOT,
        text=True,
    )
    paths: list[Path] = []
    for line in out.splitlines():
        if line.startswith(".cursor/"):
            continue
        p = ROOT / line
        if p.name == "LICENSE":
            continue
        if p.suffix in EXT_STYLE or p.name in {"Dockerfile"} or p.suffix in {".conf", ".service"}:
            paths.append(p)
    return paths


def prepend_header(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return False

    if path.name == "Dockerfile" or path.suffix in {".conf", ".service"}:
        header = HEADERS["hash"]
    else:
        style = EXT_STYLE[path.suffix]
        header = HEADERS[style]

    if path.suffix == ".md" and text.startswith("# "):
        path.write_text(header + text, encoding="utf-8")
        return True

    path.write_text(header + ("\n" if not text.startswith("\n") and header else "") + text, encoding="utf-8")
    return True


def main() -> None:
    changed = 0
    for path in tracked_files():
        if prepend_header(path):
            changed += 1
            print(path.relative_to(ROOT))
    print(f"Updated {changed} files.")


if __name__ == "__main__":
    main()
