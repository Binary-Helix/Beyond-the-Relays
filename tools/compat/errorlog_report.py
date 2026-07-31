#!/usr/bin/env python3
"""Normalize a Stellaris error.log into a signature table; diff two logs.

A "signature" collapses volatile parts of a log line (timestamps, line
numbers, counts, quoted names) so runs are comparable. Used as the exit
gate for every compat phase: net-new signatures vs baseline must be 0.

Usage:
    python tools/compat/errorlog_report.py error.log            # report
    python tools/compat/errorlog_report.py --diff base.log new.log
    python tools/compat/errorlog_report.py error.log --md out.md

Default log location (if no path given):
    %USERPROFILE%/Documents/Paradox Interactive/Stellaris/logs/error.log
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_LOG = Path(os.path.expanduser("~")) / "Documents" / \
    "Paradox Interactive" / "Stellaris" / "logs" / "error.log"

RE_HEAD = re.compile(r"^\[(?:\d[\d:.]*)\]\[([a-z_A-Z0-9]+\.cpp):(\d+)\]:\s*(.*)$")
RE_FILE = re.compile(r'file:\s*"?([^\s",]+)')
RE_LINE_REF = re.compile(r"\b(?:line|near line):?\s*\d+")
RE_NUM = re.compile(r"\b\d+\b")


def signature(msg: str) -> str:
    """Collapse a message to a stable signature."""
    s = RE_LINE_REF.sub("line N", msg)
    s = RE_NUM.sub("N", s)
    return s.strip()[:160]


def parse(path: Path):
    """Yield (subsystem, signature, file_ref) per log line."""
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        m = RE_HEAD.match(line)
        if not m:
            continue
        subsystem, _, msg = m.groups()
        fm = RE_FILE.search(msg)
        yield subsystem, signature(msg), (fm.group(1) if fm else "")


def tally(path: Path):
    subs, sigs, files = Counter(), Counter(), Counter()
    total = 0
    for subsystem, sig, fref in parse(path):
        total += 1
        subs[subsystem] += 1
        sigs[(subsystem, sig)] += 1
        if fref:
            files[fref] += 1
    return total, subs, sigs, files


def noise_sigs(path: Path | None) -> set:
    """Signature set from a vanilla-only (no mods) run, to subtract."""
    if not path:
        return set()
    _, _, sigs, _ = tally(path)
    return set(sigs)


def fmt_report(path: Path, top: int, noise: set | None = None) -> str:
    total, subs, sigs, files = tally(path)
    if noise:
        dropped = sum(c for k, c in sigs.items() if k in noise)
        sigs = Counter({k: c for k, c in sigs.items() if k not in noise})
        subs = Counter()
        for (s, _), c in sigs.items():
            subs[s] += c
        total_note = f" ({dropped} lines matched vanilla noise floor and were excluded)"
    else:
        total_note = ""
    out = [f"# error.log report — `{path}`", "",
           f"**{total} parsed error lines**{total_note}", "",
           "## By subsystem", "", "| count | subsystem |", "|---|---|"]
    out += [f"| {c} | {s} |" for s, c in subs.most_common(top)]
    out += ["", f"## Top signatures (top {top})", "",
            "| count | subsystem | signature |", "|---|---|---|"]
    out += [f"| {c} | {s} | {sig} |" for (s, sig), c in sigs.most_common(top)]
    out += ["", f"## Most-implicated files (top {top})", "",
            "| count | file |", "|---|---|"]
    out += [f"| {c} | `{f}` |" for f, c in files.most_common(top)]
    return "\n".join(out) + "\n"


def fmt_diff(base: Path, new: Path, top: int,
             noise: set | None = None) -> tuple[str, int]:
    bt, _, bsigs, _ = tally(base)
    nt, _, nsigs, _ = tally(new)
    if noise:
        bsigs = Counter({k: c for k, c in bsigs.items() if k not in noise})
        nsigs = Counter({k: c for k, c in nsigs.items() if k not in noise})
    new_only = {k: c for k, c in nsigs.items() if k not in bsigs}
    grown = {k: (bsigs[k], c) for k, c in nsigs.items()
             if k in bsigs and c > bsigs[k]}
    gone = {k: c for k, c in bsigs.items() if k not in nsigs}
    out = [f"# error.log diff", "",
           f"baseline: `{base}` ({bt} lines) → new: `{new}` ({nt} lines)", "",
           f"**NET-NEW signatures: {len(new_only)}** "
           f"(gate: must be 0) | grown: {len(grown)} | resolved: {len(gone)}", ""]
    if new_only:
        out += ["## Net-new (FAIL the gate)", "",
                "| count | subsystem | signature |", "|---|---|---|"]
        out += [f"| {c} | {s} | {sig} |"
                for (s, sig), c in sorted(new_only.items(), key=lambda kv: -kv[1])[:top]]
    if grown:
        out += ["", "## Grown", "", "| base → new | subsystem | signature |", "|---|---|---|"]
        out += [f"| {b} → {c} | {s} | {sig} |"
                for (s, sig), (b, c) in sorted(grown.items(), key=lambda kv: -kv[1][1])[:top]]
    if gone:
        out += ["", f"## Resolved ({len(gone)} signatures)", ""]
        out += [f"- ({c}) {s}: {sig}"
                for (s, sig), c in sorted(gone.items(), key=lambda kv: -kv[1])[:top]]
    return "\n".join(out) + "\n", len(new_only)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="*", help="error.log path(s)")
    ap.add_argument("--diff", nargs=2, metavar=("BASE", "NEW"))
    ap.add_argument("--noise", help="vanilla-only error.log whose signatures are excluded")
    ap.add_argument("--md", help="also write report to this file")
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()

    noise = noise_sigs(Path(args.noise)) if args.noise else None
    if args.diff:
        report, net_new = fmt_diff(Path(args.diff[0]), Path(args.diff[1]),
                                   args.top, noise)
        rc = 1 if net_new else 0
    else:
        target = Path(args.logs[0]) if args.logs else DEFAULT_LOG
        report, rc = fmt_report(target, args.top, noise), 0

    print(report)
    if args.md:
        Path(args.md).write_text(report, encoding="utf-8")
    sys.exit(rc)


if __name__ == "__main__":
    main()
