#!/usr/bin/env python3
"""Mod-vs-vanilla collision inventory for BtR 4.4 compat work.

Enumerates files whose relative path exists in BOTH the mod repo and the
vanilla Stellaris install (i.e. hard overrides), and computes a
whitespace/line-ending-normalized divergence figure per file.

Usage:
    python tools/compat/collisions.py [--vanilla PATH] [--mod PATH]
        [--dirs common events gfx interface map flags fonts sound music]
        [--csv out.csv] [--md out.md]

Exit code 0 always (reporting tool). Re-run after every vanilla patch.
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

DEFAULT_VANILLA = r"F:\SteamLibrary\steamapps\common\Stellaris"
DEFAULT_DIRS = ["common", "events", "gfx", "interface", "map", "flags",
                "fonts", "sound", "music", "localisation"]
# extensions worth content-diffing (text script/asset formats)
TEXT_EXT = {".txt", ".gui", ".gfx", ".asset", ".yml", ".shader", ".fxh",
            ".mod", ".settings", ".sfx"}


def norm_lines(path: Path) -> list[str] | None:
    """Read a text file tolerant of BOM/CRLF; return stripped, non-empty lines.

    Returns None for files we treat as binary (undecodable or non-text ext).
    """
    if path.suffix.lower() not in TEXT_EXT:
        return None
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    for enc in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return None
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def divergence(mod: Path, van: Path) -> tuple[int, str]:
    """Return (changed-line estimate, kind). kind: identical|ws-identical|text|binary."""
    a, b = norm_lines(mod), norm_lines(van)
    if a is None or b is None:
        try:
            same = mod.read_bytes() == van.read_bytes()
        except OSError:
            return (-1, "unreadable")
        return (0, "identical") if same else (-1, "binary-differs")
    if a == b:
        try:
            return (0, "identical") if mod.read_bytes() == van.read_bytes() \
                else (0, "ws-identical")
        except OSError:
            return (0, "ws-identical")
    import difflib
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    changed = sum(max(i2 - i1, j2 - j1)
                  for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal")
    return (changed, "text")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vanilla", default=DEFAULT_VANILLA)
    ap.add_argument("--mod", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--dirs", nargs="*", default=DEFAULT_DIRS)
    ap.add_argument("--csv", help="write full inventory as CSV")
    ap.add_argument("--md", help="write markdown report")
    ap.add_argument("--top", type=int, default=30, help="top-N in stdout/md")
    args = ap.parse_args()

    mod_root, van_root = Path(args.mod), Path(args.vanilla)
    if not van_root.is_dir():
        sys.exit(f"vanilla path not found: {van_root}")

    rows = []  # (relpath, changed, kind)
    for d in args.dirs:
        mdir = mod_root / d
        if not mdir.is_dir() or not (van_root / d).is_dir():
            continue
        for mf in sorted(mdir.rglob("*")):
            if not mf.is_file():
                continue
            rel = mf.relative_to(mod_root)
            vf = van_root / rel
            if vf.is_file():
                changed, kind = divergence(mf, vf)
                rows.append((str(rel).replace("\\", "/"), changed, kind))

    by_top: dict[str, int] = {}
    for rel, _, _ in rows:
        by_top[rel.split("/")[0]] = by_top.get(rel.split("/")[0], 0) + 1

    out = io.StringIO()
    out.write(f"# Collision inventory\n\nmod: `{mod_root}`\nvanilla: `{van_root}`\n\n")
    out.write(f"**Total collisions: {len(rows)}**\n\n")
    out.write("| dir | collisions |\n|---|---|\n")
    for k, v in sorted(by_top.items(), key=lambda kv: -kv[1]):
        out.write(f"| {k} | {v} |\n")

    dead = [r for r in rows if r[2] in ("identical", "ws-identical")]
    out.write(f"\n## Deletion candidates (identical to vanilla): {len(dead)}\n\n")
    for rel, _, kind in dead:
        out.write(f"- `{rel}` ({kind})\n")

    texts = sorted((r for r in rows if r[2] == "text"), key=lambda r: -r[1])
    out.write(f"\n## Most-divergent text collisions (top {args.top})\n\n")
    out.write("| changed lines (norm.) | file |\n|---|---|\n")
    for rel, ch, _ in texts[: args.top]:
        out.write(f"| {ch} | `{rel}` |\n")

    common = [r for r in rows if r[0].startswith("common/")]
    groups: dict[str, list] = {}
    for rel, ch, kind in common:
        groups.setdefault(rel.split("/")[1], []).append((rel, ch, kind))
    out.write(f"\n## common/ collisions by subdirectory ({len(common)} files)\n\n")
    for g in sorted(groups, key=lambda g: -len(groups[g])):
        files = ", ".join(Path(r).name for r, _, _ in groups[g])
        out.write(f"- **{g}** ({len(groups[g])}): {files}\n")

    report = out.getvalue()
    print(report)
    if args.md:
        Path(args.md).write_text(report, encoding="utf-8")
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["relpath", "changed_lines_normalized", "kind"])
            w.writerows(rows)


if __name__ == "__main__":
    main()
