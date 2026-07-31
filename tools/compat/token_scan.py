#!/usr/bin/env python3
"""Deprecated-token burndown scanner for the 4.0 → 4.4 migration.

Counts live-code occurrences of tokens removed/renamed between Stellaris
4.0 and 4.4. Phase 1 is done when every count is 0. Commented-out lines
(# ...) are ignored.

Usage:
    python tools/compat/token_scan.py            # summary table
    python tools/compat/token_scan.py -v         # per-file counts
"""
from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCAN_DIRS = ["common", "events"]

# token -> (regex, note)
TOKENS: dict[str, tuple[str, str]] = {
    "promotion block":  (r"^\s*promotion\s*=\s*\{", "B-2: removed in 4.4 (unemployment rework)"),
    "demotion block":   (r"^\s*demotion\s*=\s*\{", "B-2: removed in 4.4"),
    "custom_demotion_*": (r"\bcustom_demotion_(?:loc|icon)\b", "B-2: removed with demotion"),
    "unemployment cat/key": (r"\b\w*_unemployment\b|\bunemployment_\w*\b", "B-2: category removed; migrate to forced_integration"),
    "is_capped_by_modifier": (r"\bis_capped_by_modifier\b", "B-5: -> shared_capacity_modifier"),
    "inherits_capped_modifiers_from": (r"\binherits_capped_modifiers_from\b", "B-3: -> shared_capacity_modifier"),
}

EXCLUDE_PARTS = {"COMPAT-AUDIT-4.4-PEGASUS-2026-06-17", "tools", ".git"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true", help="per-file detail")
    args = ap.parse_args()

    compiled = {name: (re.compile(rx), note) for name, (rx, note) in TOKENS.items()}
    hits: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for d in SCAN_DIRS:
        for f in (REPO / d).rglob("*.txt"):
            if EXCLUDE_PARTS & set(f.parts):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = str(f.relative_to(REPO)).replace("\\", "/")
            for line in text.splitlines():
                code = line.split("#", 1)[0]
                if not code.strip():
                    continue
                for name, (rx, _) in compiled.items():
                    n = len(rx.findall(code))
                    if n:
                        hits[name][rel] += n

    print(f"{'token':38} {'total':>6}  {'files':>5}  note")
    print("-" * 110)
    all_zero = True
    for name, (_, note) in compiled.items():
        total = sum(hits[name].values())
        if total:
            all_zero = False
        print(f"{name:38} {total:>6}  {len(hits[name]):>5}  {note}")
        if args.verbose and hits[name]:
            for rel, n in sorted(hits[name].items(), key=lambda kv: -kv[1]):
                print(f"    {n:>5}  {rel}")
    print("-" * 110)
    print("BURNDOWN COMPLETE — all counts zero" if all_zero
          else "Deprecated tokens remain (see above)")


if __name__ == "__main__":
    main()
