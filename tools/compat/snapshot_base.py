#!/usr/bin/env python3
"""Snapshot vanilla base copies of every colliding file for 3-way merges.

Given a vanilla install (ideally the OLD version the mod was written
against, e.g. 4.0.23 obtained via Steam's Betas tab or download_depot),
copies every file that collides with the mod into a base directory,
preserving relative paths. remerge tooling then uses:

    base = tools/compat/base-4.0/<rel>   (this snapshot)
    ours = <mod>/<rel>
    theirs = <current vanilla>/<rel>

Usage:
    python tools/compat/snapshot_base.py --vanilla E:\\tmp\\stellaris-4.0.23
        [--out tools/compat/base-4.0] [--dirs common events interface map gfx]
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_DIRS = ["common", "events", "interface", "map", "gfx", "flags",
                "sound", "music"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vanilla", required=True,
                    help="old vanilla install to snapshot bases from")
    ap.add_argument("--out", default=str(REPO / "tools" / "compat" / "base-4.0"))
    ap.add_argument("--dirs", nargs="*", default=DEFAULT_DIRS)
    args = ap.parse_args()

    van, out = Path(args.vanilla), Path(args.out)
    copied = 0
    for d in args.dirs:
        mdir = REPO / d
        if not mdir.is_dir():
            continue
        for mf in mdir.rglob("*"):
            if not mf.is_file():
                continue
            rel = mf.relative_to(REPO)
            vf = van / rel
            if vf.is_file():
                dst = out / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(vf, dst)
                copied += 1
    print(f"snapshotted {copied} base files into {out}")


if __name__ == "__main__":
    main()
