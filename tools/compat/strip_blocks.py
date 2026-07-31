#!/usr/bin/env python3
"""Strip removed-in-4.4 `promotion = {...}` / `demotion = {...}` blocks
(and `custom_demotion_loc` / `custom_demotion_icon` lines) from pop_jobs
files (blocker B-2).

Brace-balanced removal: finds a top-of-line `promotion =` / `demotion =`
key inside a job definition and removes through its matching closing
brace. Never touches comments-only lines outside blocks.

Usage:
    python tools/compat/strip_blocks.py --dry-run   # report only
    python tools/compat/strip_blocks.py             # edit files in place
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TARGET_GLOB = "common/pop_jobs/*.txt"
RE_BLOCK_START = re.compile(r"^\s*(promotion|demotion)\s*=\s*\{")
RE_LINE_KEY = re.compile(r"^\s*custom_demotion_(?:loc|icon)\s*=")


def brace_delta(line: str) -> int:
    """Net brace count of a line, ignoring comments and quoted strings."""
    code = line.split("#", 1)[0]
    code = re.sub(r'"[^"]*"', "", code)
    return code.count("{") - code.count("}")


def strip_file(path: Path, dry: bool) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    blocks = singles = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if RE_LINE_KEY.match(line):
            singles += 1
            i += 1
            continue
        m = RE_BLOCK_START.match(line)
        if m:
            depth = brace_delta(line)
            j = i + 1
            while depth > 0 and j < len(lines):
                depth += brace_delta(lines[j])
                j += 1
            blocks += 1
            i = j
            continue
        out.append(line)
        i += 1
    if not dry and (blocks or singles):
        path.write_text("".join(out), encoding="utf-8", newline="")
    return blocks, singles


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total_b = total_s = 0
    for f in sorted(REPO.glob(TARGET_GLOB)):
        b, s = strip_file(f, args.dry_run)
        if b or s:
            print(f"{f.relative_to(REPO)}: {b} blocks, {s} custom_demotion lines")
            total_b += b
            total_s += s
    mode = "DRY RUN — no files changed" if args.dry_run else "files edited in place"
    print(f"\nTotal: {total_b} promotion/demotion blocks, {total_s} single lines ({mode})")


if __name__ == "__main__":
    main()
