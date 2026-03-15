#!/usr/bin/env python3
"""
Binary Helix / BtR — Stellaris Patch Compatibility Analyzer
============================================================
Compares two vanilla Stellaris installations (old vs new patch) against
your mod directory to identify conflicts, risks, and opportunities.

Usage:
    python btr_analyzer.py --old <old_vanilla_dir> --new <new_vanilla_dir> --mod <mod_dir> [--out report.html]

For version acquisition help:
    python btr_analyzer.py --help-versions
"""

import argparse
import hashlib
import html as html_lib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# File extensions considered "mod-relevant" (script, data, localisation)
MOD_RELEVANT_EXTENSIONS = {
    ".txt", ".csv", ".yml", ".yaml", ".json",
    ".gfx", ".gui", ".sfx", ".asset", ".shader",
    ".mod", ".trigger", ".effect"
}

# Extensions to skip for diffing (binary / large assets)
BINARY_EXTENSIONS = {
    ".dds", ".png", ".jpg", ".jpeg", ".bmp", ".tga",
    ".ogg", ".wav", ".mp3",
    ".mesh", ".pdx",
    ".exe", ".dll",
}

# Stellaris directory categories and their human labels (for report grouping)
DIR_CATEGORY_MAP = {
    "common":           "Common (Game Rules & Content)",
    "events":           "Events",
    "map":              "Map & Galaxies",
    "localisation":     "Localisation",
    "interface":        "Interface / GUI",
    "gfx":              "Graphics Definitions",
    "sound":            "Sound",
    "prescripted_countries": "Prescripted Empires",
    "flags":            "Flags",
    "fonts":            "Fonts",
    "music":            "Music",
}

SEVERITY_CRITICAL    = "CRITICAL CONFLICT"
SEVERITY_TENURED     = "TENURED CONFLICT"
SEVERITY_TANGENTIAL  = "TANGENTIAL CONFLICT"
SEVERITY_ADOPT       = "NEW VANILLA CONTENT"
SEVERITY_DELETED     = "VANILLA FILE DELETED"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FileDiff:
    rel_path: str                   # Path relative to game root
    category: str                   # Top-level dir (common, events, …)
    change_type: str                # added | modified | deleted
    mod_status: str                 # direct_conflict | watch | none
    severity: str                   # human severity label
    old_hash: Optional[str] = None
    new_hash:  Optional[str] = None
    # Raw file contents stored for on-demand JS diffing (None = binary/unreadable)
    old_text: Optional[str] = None
    new_text: Optional[str] = None
    mod_file: Optional[str] = None  # Path of the conflicting mod file
    diff_label: Optional[str] = None  # Custom label describing what sides of the diff represent


@dataclass
class Report:
    generated_at: str
    old_label: str
    new_label: str
    mod_name: str
    total_vanilla_changed: int = 0
    critical_conflicts: list[FileDiff] = field(default_factory=list)   # mod file + vanilla changed this patch
    tenured_conflicts: list[FileDiff] = field(default_factory=list)    # mod file + vanilla unchanged this patch
    tangential_conflicts: list[FileDiff] = field(default_factory=list) # vanilla files in mod-touched folders, no mod override
    new_vanilla: list[FileDiff] = field(default_factory=list)          # brand-new vanilla files
    deleted_vanilla: list[FileDiff] = field(default_factory=list)      # vanilla files removed


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def file_hash(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def is_binary(path: Path) -> bool:
    return path.suffix.lower() in BINARY_EXTENSIONS


def safe_read_text(path: Optional[Path]) -> Optional[str]:
    """Read a text file with encoding fallback. Returns None for binary/unreadable."""
    if path is None or is_binary(path):
        return None
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return None


def safe_read(path: Path) -> Optional[list[str]]:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=enc).splitlines(keepends=True)
        except Exception:
            continue
    return None


def build_file_index(root: Path) -> dict[str, Path]:
    """Returns {relative_path_str: absolute_path} for all files under root."""
    index = {}
    for p in root.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(root)).replace("\\", "/")
            index[rel] = p
    return index


def get_category(rel_path: str) -> str:
    parts = rel_path.split("/")
    return parts[0] if parts else "other"


def build_mod_index(mod_dir: Path) -> dict[str, Path]:
    """
    Build an index of mod files.  Keys are normalised to their relative path
    within the mod directory so they can be matched against vanilla rel paths.
    """
    return build_file_index(mod_dir)


def find_mod_match(rel_path: str, mod_index: dict[str, Path]) -> Optional[str]:
    """
    Check whether the mod overrides a specific vanilla rel_path.
    Stellaris mods mirror the vanilla directory structure, so a direct key
    match is the primary check.  We also do a basename-only fuzzy match for
    files that live in dynamic subdirs (e.g. localisation language folders).
    """
    # Direct match
    if rel_path in mod_index:
        return rel_path

    # Basename match (catches localisation/english/foo.yml vs localisation/foo.yml etc.)
    basename = Path(rel_path).name
    for mod_rel in mod_index:
        if Path(mod_rel).name == basename:
            return mod_rel

    return None


def analyze(old_dir: Path, new_dir: Path, mod_dir: Path,
            old_label: str, new_label: str) -> Report:

    print(f"  Indexing OLD vanilla ({old_dir.name}) …", flush=True)
    old_index = build_file_index(old_dir)
    print(f"    {len(old_index):,} files found")

    print(f"  Indexing NEW vanilla ({new_dir.name}) …", flush=True)
    new_index = build_file_index(new_dir)
    print(f"    {len(new_index):,} files found")

    print(f"  Indexing mod ({mod_dir.name}) …", flush=True)
    mod_index = build_mod_index(mod_dir)
    print(f"    {len(mod_index):,} mod files found")

    all_rels = set(old_index) | set(new_index)
    report = Report(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        old_label=old_label,
        new_label=new_label,
        mod_name=mod_dir.name,
    )

    # Pre-compute mod categories once (avoid O(n²) recompute inside loop)
    mod_categories = {get_category(k) for k in mod_index}

    all_rels_sorted = sorted(all_rels)
    total = len(all_rels_sorted)
    print(f"  Comparing {total:,} file paths …", flush=True)
    PROGRESS_INTERVAL = 1000

    for i, rel in enumerate(all_rels_sorted, 1):
        if i % PROGRESS_INTERVAL == 0:
            print(f"    {i:,} / {total:,} …", flush=True)

        ext = Path(rel).suffix.lower()
        in_old = rel in old_index
        in_new = rel in new_index

        # Determine change type via hash (hash only; no reading content yet)
        if in_old and in_new:
            old_h = file_hash(old_index[rel])
            new_h = file_hash(new_index[rel])
            if old_h == new_h:
                continue  # Unchanged — skip entirely
            change_type = "modified"
        elif in_new:
            change_type = "added"
            old_h, new_h = None, file_hash(new_index[rel])
        else:
            change_type = "deleted"
            old_h, new_h = file_hash(old_index[rel]), None

        report.total_vanilla_changed += 1
        category = get_category(rel)
        is_relevant = ext in MOD_RELEVANT_EXTENSIONS or ext == ""
        mod_match = find_mod_match(rel, mod_index)

        # Read file text ONLY for relevant text files that will appear in report.
        # Diffs are computed later in the browser — we just need the raw content.
        def read_texts():
            old_t = safe_read_text(old_index.get(rel)) if in_old else None
            new_t = safe_read_text(new_index.get(rel)) if in_new else None
            return old_t, new_t

        if mod_match:
            old_t, new_t = read_texts()
            # Critical = vanilla changed in this patch AND mod has an override.
            # Tenured  = vanilla was NOT changed in this patch, but mod still overrides it.
            if change_type == "modified":
                severity = SEVERITY_CRITICAL
                mod_status = "critical_conflict"
                target_list = report.critical_conflicts
            else:
                # change_type == "added": new vanilla file that mod already has — critical
                # change_type == "deleted": mod overrides a now-deleted vanilla — also critical
                severity = SEVERITY_CRITICAL
                mod_status = "critical_conflict"
                target_list = report.critical_conflicts
            fd = FileDiff(
                rel_path=rel, category=category,
                change_type=change_type,
                mod_status=mod_status, severity=severity,
                old_hash=old_h, new_hash=new_h,
                old_text=old_t, new_text=new_t,
                mod_file=mod_match,
            )
            target_list.append(fd)

        elif change_type == "deleted":
            fd = FileDiff(
                rel_path=rel, category=category,
                change_type=change_type,
                mod_status="none", severity=SEVERITY_DELETED,
                old_hash=old_h, new_hash=None,
            )
            report.deleted_vanilla.append(fd)

        elif change_type == "added" and is_relevant:
            old_t, new_t = read_texts()
            fd = FileDiff(
                rel_path=rel, category=category,
                change_type=change_type,
                mod_status="none", severity=SEVERITY_ADOPT,
                old_hash=None, new_hash=new_h,
                old_text=old_t, new_text=new_t,
            )
            report.new_vanilla.append(fd)

        elif change_type == "modified" and is_relevant:
            if category in mod_categories:
                old_t, new_t = read_texts()
                fd = FileDiff(
                    rel_path=rel, category=category,
                    change_type=change_type,
                    mod_status="tangential", severity=SEVERITY_TANGENTIAL,
                    old_hash=old_h, new_hash=new_h,
                    old_text=old_t, new_text=new_t,
                )
                report.tangential_conflicts.append(fd)

    # --- Tenured conflicts: mod overrides vanilla files that have NOT changed this patch ---
    # These are files present in both old+new with the same hash but overridden by mod.
    print(f"  Scanning for tenured conflicts (mod overrides with no patch change) …", flush=True)
    all_unchanged_vanilla = {
        rel for rel in old_index
        if rel in new_index and file_hash(old_index[rel]) == file_hash(new_index[rel])
    }
    for rel in sorted(all_unchanged_vanilla):
        mod_match = find_mod_match(rel, mod_index)
        if not mod_match:
            continue
        ext = Path(rel).suffix.lower()
        if ext not in MOD_RELEVANT_EXTENSIONS and ext != "":
            continue
        category = get_category(rel)
        old_t = safe_read_text(old_index[rel])                           # vanilla (unchanged)
        mod_t = safe_read_text(mod_index[mod_match]) if mod_match else None  # mod override
        fd = FileDiff(
            rel_path=rel, category=category,
            change_type="unchanged",
            mod_status="tenured_conflict", severity=SEVERITY_TENURED,
            old_hash=file_hash(old_index[rel]), new_hash=file_hash(new_index[rel]),
            old_text=old_t,                    # vanilla content (left side of diff)
            new_text=mod_t,                    # mod override content (right side of diff)
            mod_file=mod_match,
            diff_label="Vanilla (unchanged) vs Mod Override",
        )
        report.tenured_conflicts.append(fd)

    report.critical_conflicts.sort(key=lambda x: x.rel_path.lower())
    report.tenured_conflicts.sort(key=lambda x: x.rel_path.lower())
    report.tangential_conflicts.sort(key=lambda x: x.rel_path.lower())
    report.new_vanilla.sort(key=lambda x: x.rel_path.lower())
    report.deleted_vanilla.sort(key=lambda x: x.rel_path.lower())

    print(f"\n  Results:")
    print(f"    Critical conflicts  : {len(report.critical_conflicts)}")
    print(f"    Tenured conflicts   : {len(report.tenured_conflicts)}")
    print(f"    Tangential conflicts: {len(report.tangential_conflicts)}")
    print(f"    New vanilla files   : {len(report.new_vanilla)}")
    print(f"    Deleted vanilla     : {len(report.deleted_vanilla)}")

    return report


# ---------------------------------------------------------------------------
# HTML Report Generation
# ---------------------------------------------------------------------------

JS_BLOCK = r"""<script>
// ── Minimal unified-diff engine (runs in browser on demand) ──────────────
function computeDiff(oldText, newText, maxLines) {
  maxLines = maxLines || 400;
  const oldLines = oldText ? oldText.split('\n') : [];
  const newLines = newText ? newText.split('\n') : [];

  // LCS-based diff via simple DP (sufficient for Stellaris script files)
  function lcs(a, b) {
    const m = a.length, n = b.length;
    const dp = Array.from({length: m+1}, () => new Uint32Array(n+1));
    for (let i = m-1; i >= 0; i--)
      for (let j = n-1; j >= 0; j--)
        dp[i][j] = a[i] === b[j] ? dp[i+1][j+1]+1 : Math.max(dp[i+1][j], dp[i][j+1]);
    const ops = [];
    let i = 0, j = 0;
    while (i < m || j < n) {
      if (i < m && j < n && a[i] === b[j]) { ops.push([' ', a[i]]); i++; j++; }
      else if (j < n && (i >= m || dp[i][j+1] >= dp[i+1][j])) { ops.push(['+', b[j]]); j++; }
      else { ops.push(['-', a[i]]); i++; }
    }
    return ops;
  }

  const ops = lcs(oldLines, newLines);
  const CTX = 3;
  // Group into hunks with context
  const changed = ops.map((o,i) => o[0] !== ' ' ? i : -1).filter(i => i >= 0);
  if (!changed.length) return {html: '<div class="no-diff-msg">Files are identical.</div>', adds:0, dels:0};

  let adds = 0, dels = 0;
  let hunkRanges = [];
  changed.forEach(ci => {
    const s = Math.max(0, ci-CTX), e = Math.min(ops.length-1, ci+CTX);
    if (hunkRanges.length && s <= hunkRanges[hunkRanges.length-1][1]+1)
      hunkRanges[hunkRanges.length-1][1] = e;
    else
      hunkRanges.push([s, e]);
  });

  // Build line-number maps: ops index -> old line number, new line number
  // ops entries are [op, text] where op is ' ', '+', or '-'
  const oldLineNums = new Array(ops.length);
  const newLineNums = new Array(ops.length);
  let oldN = 1, newN = 1;
  for (let k = 0; k < ops.length; k++) {
    const op = ops[k][0];
    oldLineNums[k] = oldN;
    newLineNums[k] = newN;
    if (op === ' ') { oldN++; newN++; }
    else if (op === '-') { oldN++; }
    else { newN++; }
  }

  let linesOut = [];
  hunkRanges.forEach(([s, e]) => {
    // Count old/new lines in this hunk for the @@ header
    let oldStart = oldLineNums[s], newStart = newLineNums[s];
    let oldCount = 0, newCount = 0;
    for (let k = s; k <= e; k++) {
      const op = ops[k][0];
      if (op === ' ') { oldCount++; newCount++; }
      else if (op === '-') { oldCount++; }
      else { newCount++; }
    }
    linesOut.push({t:'hunk', v:`@@ -${oldStart},${oldCount} +${newStart},${newCount} @@`});
    for (let k = s; k <= e; k++) {
      const [op, txt] = ops[k];
      const lineNum = op === '+' ? newLineNums[k] : oldLineNums[k];
      if (op === '+') { adds++; linesOut.push({t:'add', n:lineNum, v:'+'+txt}); }
      else if (op === '-') { dels++; linesOut.push({t:'del', n:lineNum, v:'-'+txt}); }
      else linesOut.push({t:'ctx', n:oldLineNums[k], v:' '+txt});
    }
  });

  const truncated = linesOut.length > maxLines;
  if (truncated) linesOut = linesOut.slice(0, maxLines);

  const htmlLines = linesOut.map(l => {
    const cls = l.t==='add' ? 'diff-line diff-line-add'
              : l.t==='del' ? 'diff-line diff-line-del'
              : l.t==='hunk'? 'diff-line diff-line-hunk'
              : 'diff-line';
    const esc = l.v.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    const gutter = l.t==='hunk' ? '' : String(l.n);
    return `<span class="${cls}"><span class="ln">${gutter}</span>${esc}</span>`;
  }).join('');

  const truncMsg = truncated ? `<div class="no-diff-msg">… diff truncated at ${maxLines} lines</div>` : '';
  return {
    html: `<div class="diff-code"><pre>${htmlLines}</pre></div>${truncMsg}`,
    adds, dels
  };
}

function toggleDiff(el) {
  const item = el.closest('.file-item');
  const wasOpen = item.classList.contains('open');
  item.classList.toggle('open');

  if (!wasOpen) {
    const body  = item.querySelector('.diff-body');
    const dataEl = item.querySelector('.diff-data');
    if (!dataEl) return;  // binary / no data

    // Already rendered
    if (body.dataset.rendered) return;
    body.dataset.rendered = '1';

    const data = JSON.parse(dataEl.innerHTML);
    const result = computeDiff(data.old, data.new);

    // Update meta line with counts
    const meta = item.querySelector('.diff-meta');
    if (meta && (result.adds || result.dels)) {
      const existing = meta.querySelector('.diff-counts');
      if (!existing) {
        const span = document.createElement('span');
        span.className = 'diff-counts';
        span.innerHTML = `Changes: <span style="color:var(--green)">+${result.adds}</span> / <span style="color:var(--red)">-${result.dels}</span>`;
        meta.appendChild(document.createTextNode('\u00a0·\u00a0'));
        meta.appendChild(span);
      }
    }

    body.innerHTML = result.html;
  }
}

function toggleSection(id) {
  const body = document.getElementById('body-' + id);
  body.style.display = body.style.display === 'none' ? '' : 'none';
}

function filterList(listId, category) {
  const list = document.getElementById(listId);
  const items = list.querySelectorAll('.file-item');
  items.forEach(item => {
    if (category === 'all' || item.dataset.category === category) {
      item.style.display = '';
    } else {
      item.style.display = 'none';
    }
  });
  const bar = list.previousElementSibling;
  if (bar && bar.classList.contains('filter-bar')) {
    bar.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    bar.querySelector('[data-cat="' + category + '"]').classList.add('active');
  }
}
</script>"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BtR Patch Compatibility Report — {old_label} → {new_label}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;400;600;700;900&display=swap');

  :root {{
    --bg:          #090c12;
    --surface:     #0e1420;
    --surface2:    #131a28;
    --border:      #1e2d45;
    --accent:      #4af0c4;
    --accent2:     #1a7aff;
    --red:         #ff4466;
    --orange:      #ff8c42;
    --yellow:      #ffe566;
    --green:       #4af0c4;
    --dim:         #4a6080;
    --text:        #cdd9e8;
    --text-dim:    #6b8299;
    --mono:        'Share Tech Mono', monospace;
    --sans:        'Exo 2', sans-serif;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    font-size: 14px;
    line-height: 1.6;
    min-height: 100vh;
  }}

  /* ── HEADER ── */
  header {{
    background: linear-gradient(135deg, #060912 0%, #0a1525 50%, #060e1c 100%);
    border-bottom: 1px solid var(--border);
    padding: 32px 40px 28px;
    position: relative;
    overflow: hidden;
  }}
  header::before {{
    content: '';
    position: absolute; inset: 0;
    background:
      repeating-linear-gradient(90deg, transparent, transparent 40px, rgba(74,240,196,.03) 40px, rgba(74,240,196,.03) 41px),
      repeating-linear-gradient(0deg,  transparent, transparent 40px, rgba(74,240,196,.03) 40px, rgba(74,240,196,.03) 41px);
    pointer-events: none;
  }}
  .header-tag {{
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 3px;
    color: var(--accent);
    opacity: .7;
    margin-bottom: 8px;
    text-transform: uppercase;
  }}
  header h1 {{
    font-size: 28px;
    font-weight: 900;
    letter-spacing: 1px;
    color: #fff;
    margin-bottom: 4px;
  }}
  header h1 span {{ color: var(--accent); }}
  .header-sub {{
    font-family: var(--mono);
    font-size: 12px;
    color: var(--text-dim);
    margin-top: 6px;
  }}
  .patch-arrow {{
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-top: 14px;
    background: rgba(74,240,196,.06);
    border: 1px solid rgba(74,240,196,.15);
    border-radius: 4px;
    padding: 6px 16px;
    font-family: var(--mono);
    font-size: 13px;
  }}
  .patch-arrow .v-old {{ color: var(--red); }}
  .patch-arrow .arrow  {{ color: var(--dim); }}
  .patch-arrow .v-new  {{ color: var(--green); }}

  /* ── LAYOUT ── */
  .container {{ max-width: 1400px; margin: 0 auto; padding: 32px 40px; }}

  /* ── SUMMARY CARDS ── */
  .summary-grid {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-bottom: 36px;
  }}
  .stat-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
  }}
  .stat-card::after {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
  }}
  .stat-card.red::after   {{ background: var(--red); }}
  .stat-card.orange::after {{ background: var(--orange); }}
  .stat-card.green::after  {{ background: var(--green); }}
  .stat-card.yellow::after {{ background: var(--yellow); }}
  .stat-card.blue::after   {{ background: var(--accent2); }}
  .stat-label {{
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 8px;
    font-family: var(--mono);
  }}
  .stat-num {{
    font-size: 40px;
    font-weight: 900;
    line-height: 1;
    margin-bottom: 4px;
  }}
  .stat-card.red    .stat-num {{ color: var(--red); }}
  .stat-card.orange .stat-num {{ color: var(--orange); }}
  .stat-card.green  .stat-num {{ color: var(--green); }}
  .stat-card.yellow .stat-num {{ color: var(--yellow); }}
  .stat-card.blue   .stat-num {{ color: var(--accent2); }}
  .stat-desc {{
    font-size: 11px;
    color: var(--text-dim);
  }}

  /* ── SECTIONS ── */
  .section {{
    margin-bottom: 40px;
  }}
  .section-header {{
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }}
  .section-badge {{
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 2px;
    padding: 3px 10px;
    border-radius: 3px;
    text-transform: uppercase;
    font-weight: 600;
  }}
  .badge-red    {{ background: rgba(255,68,102,.12); color: var(--red);    border: 1px solid rgba(255,68,102,.3); }}
  .badge-orange {{ background: rgba(255,140,66,.12); color: var(--orange); border: 1px solid rgba(255,140,66,.3); }}
  .badge-yellow {{ background: rgba(255,229,102,.12); color: var(--yellow); border: 1px solid rgba(255,229,102,.3); }}
  .badge-green  {{ background: rgba(74,240,196,.10); color: var(--green);  border: 1px solid rgba(74,240,196,.2); }}
  .badge-blue   {{ background: rgba(26,122,255,.12); color: var(--accent2);border: 1px solid rgba(26,122,255,.3); }}
  .section-title {{
    font-size: 16px;
    font-weight: 700;
    color: #fff;
  }}
  .section-count {{
    font-family: var(--mono);
    font-size: 12px;
    color: var(--text-dim);
    margin-left: auto;
  }}

  /* ── FILE TABLE ── */
  .file-list {{ display: flex; flex-direction: column; gap: 4px; }}

  .file-item {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    overflow: hidden;
    transition: border-color .15s;
  }}
  .file-item:hover {{ border-color: var(--dim); }}
  .file-item.conflict {{ border-left: 3px solid var(--red); }}
  .file-item.watch    {{ border-left: 3px solid var(--orange); }}
  .file-item.new      {{ border-left: 3px solid var(--green); }}
  .file-item.deleted  {{ border-left: 3px solid var(--accent2); }}

  .file-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    cursor: pointer;
    user-select: none;
  }}
  .file-header:hover {{ background: var(--surface2); }}

  .change-pill {{
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 1px;
    padding: 2px 7px;
    border-radius: 2px;
    text-transform: uppercase;
    flex-shrink: 0;
  }}
  .pill-modified {{ background: rgba(255,229,102,.1); color: var(--yellow);  border: 1px solid rgba(255,229,102,.25); }}
  .pill-added    {{ background: rgba(74,240,196,.1);  color: var(--green);   border: 1px solid rgba(74,240,196,.2); }}
  .pill-deleted  {{ background: rgba(26,122,255,.1);  color: var(--accent2); border: 1px solid rgba(26,122,255,.2); }}

  .file-path {{
    font-family: var(--mono);
    font-size: 12px;
    color: var(--text);
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  .file-path .dir {{ color: var(--text-dim); }}
  .file-path .name {{ color: #e8f0ff; }}

  .diff-stats {{
    font-family: var(--mono);
    font-size: 11px;
    display: flex;
    gap: 8px;
    flex-shrink: 0;
  }}
  .diff-stats .adds {{ color: var(--green); }}
  .diff-stats .dels {{ color: var(--red); }}

  .mod-conflict-badge {{
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 1px;
    padding: 2px 7px;
    border-radius: 2px;
    background: rgba(255,68,102,.1);
    color: var(--red);
    border: 1px solid rgba(255,68,102,.2);
    flex-shrink: 0;
  }}

  .expand-icon {{
    color: var(--dim);
    font-size: 10px;
    flex-shrink: 0;
    transition: transform .2s;
  }}
  .file-item.open .expand-icon {{ transform: rotate(90deg); }}

  /* ── DIFF PANEL ── */
  .diff-panel {{
    display: none;
    border-top: 1px solid var(--border);
    background: #07090f;
  }}
  .file-item.open .diff-panel {{ display: block; }}

  .diff-meta {{
    padding: 8px 14px;
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text-dim);
    background: var(--surface2);
    border-bottom: 1px solid var(--border);
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
  }}
  .diff-meta span {{ color: var(--text); }}
  .diff-label-note {{
    width: 100%;
    margin-top: 2px;
    font-size: 10px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--orange);
    opacity: 0.9;
  }}

  .diff-code {{
    overflow-x: auto;
    padding: 12px 0;
    max-height: 600px;
    overflow-y: auto;
  }}
  .diff-code pre {{
    font-family: var(--mono);
    font-size: 11px;
    line-height: 1.7;
    white-space: pre;
    padding: 0 14px;
  }}
  .diff-line       {{ display: block; padding: 0 4px; border-radius: 2px; white-space: pre; }}
  .diff-line-add   {{ color: #66ffcc; background: rgba(74,240,196,.06); }}
  .diff-line-del   {{ color: #ff8899; background: rgba(255,68,102,.06); }}
  .diff-line-hunk  {{ color: var(--accent2); opacity: .7; padding-left: 52px; }}
  .diff-line-meta  {{ color: var(--dim); }}
  .ln {{
    display: inline-block;
    width: 44px;
    min-width: 44px;
    padding-right: 12px;
    text-align: right;
    color: var(--dim);
    font-size: 10px;
    user-select: none;
    border-right: 1px solid var(--border);
    margin-right: 10px;
  }}

  .no-diff-msg {{
    padding: 20px 14px;
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text-dim);
    font-style: italic;
  }}

  .diff-loading {{
    padding: 16px 14px;
    font-family: var(--mono);
    font-size: 11px;
    color: var(--dim);
  }}

  /* ── CATEGORY FILTER BAR ── */
  .filter-bar {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 14px;
    flex-wrap: wrap;
  }}
  .filter-label {{
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 1px;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-right: 4px;
  }}
  .filter-btn {{
    font-family: var(--mono);
    font-size: 10px;
    padding: 3px 10px;
    border-radius: 3px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-dim);
    cursor: pointer;
    transition: all .15s;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}
  .filter-btn:hover,
  .filter-btn.active {{
    background: rgba(74,240,196,.08);
    border-color: var(--accent);
    color: var(--accent);
  }}

  /* ── HELP BOX ── */
  .help-box {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 20px 24px;
    margin-bottom: 36px;
    font-size: 13px;
  }}
  .help-box h3 {{
    font-size: 13px;
    font-weight: 700;
    color: var(--accent);
    margin-bottom: 10px;
    font-family: var(--mono);
    letter-spacing: 1px;
    text-transform: uppercase;
  }}
  .help-box p {{ color: var(--text-dim); line-height: 1.7; margin-bottom: 8px; }}
  .help-box code {{
    font-family: var(--mono);
    font-size: 11px;
    background: rgba(74,240,196,.06);
    border: 1px solid rgba(74,240,196,.15);
    padding: 2px 6px;
    border-radius: 3px;
    color: var(--accent);
  }}

  /* ── FOOTER ── */
  footer {{
    border-top: 1px solid var(--border);
    padding: 20px 40px;
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text-dim);
    display: flex;
    justify-content: space-between;
  }}

  /* ── COLLAPSIBLE SECTION ── */
  .section-toggle {{
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }}
  .section-toggle:hover .section-title {{ color: var(--accent); }}

  /* ── EMPTY STATE ── */
  .empty-state {{
    padding: 32px;
    text-align: center;
    font-family: var(--mono);
    font-size: 12px;
    color: var(--text-dim);
    border: 1px dashed var(--border);
    border-radius: 4px;
  }}
</style>
</head>
<body>

<header>
  <div class="header-tag">Binary Helix Mod // Stellaris Patch Analyzer</div>
  <h1>Patch Compatibility <span>Report</span></h1>
  <div class="header-sub">Generated {generated_at} &nbsp;·&nbsp; Mod: {mod_name}</div>
  <div class="patch-arrow">
    <span class="v-old">{old_label}</span>
    <span class="arrow">────▶</span>
    <span class="v-new">{new_label}</span>
  </div>
</header>

<div class="container">

  <!-- Summary Cards -->
  <div class="summary-grid">
    <div class="stat-card red">
      <div class="stat-label">Critical Conflicts</div>
      <div class="stat-num">{n_critical}</div>
      <div class="stat-desc">Mod overrides vanilla files Paradox changed this patch</div>
    </div>
    <div class="stat-card orange">
      <div class="stat-label">Tenured Conflicts</div>
      <div class="stat-num">{n_tenured}</div>
      <div class="stat-desc">Mod overrides vanilla files untouched this patch</div>
    </div>
    <div class="stat-card yellow">
      <div class="stat-label">Tangential Conflicts</div>
      <div class="stat-num">{n_tangential}</div>
      <div class="stat-desc">Vanilla files in mod-touched folders with no mod override</div>
    </div>
    <div class="stat-card green">
      <div class="stat-label">New Vanilla Content</div>
      <div class="stat-num">{n_new}</div>
      <div class="stat-desc">Brand-new vanilla files to review for integration</div>
    </div>
    <div class="stat-card blue">
      <div class="stat-label">Vanilla Files Deleted</div>
      <div class="stat-num">{n_deleted}</div>
      <div class="stat-desc">Vanilla files removed — check for broken references</div>
    </div>
  </div>

  {version_help}

  <!-- SECTION: Critical Conflicts -->
  <div class="section" id="sec-critical">
    <div class="section-toggle" onclick="toggleSection('critical')">
      <span class="section-badge badge-red">⚠ Priority 1</span>
      <span class="section-title">Critical Conflicts</span>
      <span class="section-count">{n_critical} files &nbsp; ▶</span>
    </div>
    <div id="body-critical">
      {filter_bar_critical}
      <div class="file-list" id="list-critical">
        {critical_items}
      </div>
    </div>
  </div>

  <!-- SECTION: Tenured Conflicts -->
  <div class="section" id="sec-tenured">
    <div class="section-toggle" onclick="toggleSection('tenured')">
      <span class="section-badge badge-orange">⚡ Priority 2</span>
      <span class="section-title">Tenured Conflicts</span>
      <span class="section-count">{n_tenured} files &nbsp; ▶</span>
    </div>
    <div id="body-tenured">
      {filter_bar_tenured}
      <div class="file-list" id="list-tenured">
        {tenured_items}
      </div>
    </div>
  </div>

  <!-- SECTION: Tangential Conflicts -->
  <div class="section" id="sec-tangential">
    <div class="section-toggle" onclick="toggleSection('tangential')">
      <span class="section-badge badge-yellow">◈ Priority 3</span>
      <span class="section-title">Tangential Conflicts</span>
      <span class="section-count">{n_tangential} files &nbsp; ▶</span>
    </div>
    <div id="body-tangential">
      {filter_bar_tangential}
      <div class="file-list" id="list-tangential">
        {tangential_items}
      </div>
    </div>
  </div>

  <!-- SECTION: New Vanilla Content -->
  <div class="section" id="sec-new">
    <div class="section-toggle" onclick="toggleSection('new')">
      <span class="section-badge badge-green">✦ Opportunity</span>
      <span class="section-title">New Vanilla Content</span>
      <span class="section-count">{n_new} files &nbsp; ▶</span>
    </div>
    <div id="body-new">
      {filter_bar_new}
      <div class="file-list" id="list-new">
        {new_items}
      </div>
    </div>
  </div>

  <!-- SECTION: Deleted Vanilla -->
  <div class="section" id="sec-deleted">
    <div class="section-toggle" onclick="toggleSection('deleted')">
      <span class="section-badge badge-blue">✕ Removed</span>
      <span class="section-title">Vanilla Files Deleted</span>
      <span class="section-count">{n_deleted} files &nbsp; ▶</span>
    </div>
    <div id="body-deleted">
      <div class="file-list" id="list-deleted">
        {deleted_items}
      </div>
    </div>
  </div>

</div>

<footer>
  <span>BtR Patch Analyzer · Binary Helix Mod Team</span>
  <span>{old_label} → {new_label} · {total_changed} vanilla files changed</span>
</footer>

{script_block}
</body>
</html>
"""


def format_path(rel_path: str) -> str:
    parts = rel_path.split("/")
    if len(parts) > 1:
        dir_part = html_lib.escape("/".join(parts[:-1]) + "/")
        name_part = html_lib.escape(parts[-1])
        return f'<span class="dir">{dir_part}</span><span class="name">{name_part}</span>'
    return f'<span class="name">{html_lib.escape(rel_path)}</span>'


def render_file_item(fd: FileDiff, css_class: str) -> str:
    pill_cls = f"pill-{fd.change_type}"

    meta_parts = [f"Category: <span>{html_lib.escape(fd.category)}</span>"]
    if fd.mod_file:
        meta_parts.append(f"Mod override: <span>{html_lib.escape(fd.mod_file)}</span>")

    conflict_badge = '<span class="mod-conflict-badge">MOD OVERRIDE</span>' if fd.mod_file else ""

    # Embed raw text inside a <template> tag (inert HTML - parser never tokenises
    # its content, so raw newlines and special chars in file text are fully safe).
    has_text = fd.old_text is not None or fd.new_text is not None
    if has_text:
        payload = json.dumps({
            "old": fd.old_text or "",
            "new": fd.new_text or "",
            "rel": fd.rel_path,
        }, ensure_ascii=False)
        safe_payload = html_lib.escape(payload, quote=False)
        diff_panel_content = (
            f'<div class="diff-loading">Click to expand diff…</div>'
            f'<template class="diff-data">{safe_payload}</template>'
        )
    else:
        diff_panel_content = '<div class="no-diff-msg">Binary or non-text file — no diff available.</div>'

    return f'''
<div class="file-item {css_class}" data-category="{html_lib.escape(fd.category)}">
  <div class="file-header" onclick="toggleDiff(this)">
    <span class="change-pill {pill_cls}">{fd.change_type}</span>
    <span class="file-path">{format_path(fd.rel_path)}</span>
    {conflict_badge}
    <span class="expand-icon">▶</span>
  </div>
  <div class="diff-panel">
    <div class="diff-meta">{"&nbsp;·&nbsp;".join(meta_parts)}{f'<div class="diff-label-note">{html_lib.escape(fd.diff_label)}</div>' if fd.diff_label else ""}</div>
    <div class="diff-body">{diff_panel_content}</div>
  </div>
</div>'''


def build_filter_bar(items: list[FileDiff], list_id: str) -> str:
    if not items:
        return ""
    cats = sorted({fd.category for fd in items})
    if len(cats) <= 1:
        return ""
    btns = [f'<button class="filter-btn active" data-cat="all" onclick="filterList(\'{list_id}\', \'all\')">All</button>']
    for c in cats:
        n = sum(1 for fd in items if fd.category == c)
        label = DIR_CATEGORY_MAP.get(c, c)
        btns.append(
            f'<button class="filter-btn" data-cat="{html_lib.escape(c)}" '
            f'onclick="filterList(\'{list_id}\', \'{html_lib.escape(c)}\')">'
            f'{html_lib.escape(label)} ({n})</button>'
        )
    return f'<div class="filter-bar"><span class="filter-label">Filter:</span>{"".join(btns)}</div>'


VERSION_HELP_HTML = """
<div class="help-box">
  <h3>⬇  How to Obtain the Previous Vanilla Version</h3>
  <p>Stellaris does not keep old versions installed by default. The easiest way to pull any
     specific patch is <strong>DepotDownloader</strong> (free, open-source, no Steam login required for public depots):</p>
  <p>
    1. Download from <code>github.com/SteamRE/DepotDownloader</code><br>
    2. Look up the old manifest ID on <code>steamdb.info/app/281990/depots/</code> — find the depot for your OS, pick the patch date.<br>
    3. Run: <code>DepotDownloader.exe -app 281990 -depot 281991 -manifest &lt;MANIFEST_ID&gt; -dir ./stellaris_old</code><br>
    4. Point this script at <code>./stellaris_old</code> as <code>--old</code> and your current install as <code>--new</code>.
  </p>
  <p>Alternatively, if you use <strong>steamctl</strong> (Python): <code>pip install steamctl</code> then
     <code>steamctl depot download -a 281990 -d 281991 -m &lt;MANIFEST_ID&gt;</code></p>
</div>
"""


def generate_html(report: Report, include_version_help: bool) -> str:
    def items_or_empty(items, css_class):
        if not items:
            return '<div class="empty-state">No items in this category.</div>'
        return "\n".join(render_file_item(fd, css_class) for fd in items)

    return HTML_TEMPLATE.format(
        script_block=JS_BLOCK,
        old_label=html_lib.escape(report.old_label),
        new_label=html_lib.escape(report.new_label),
        mod_name=html_lib.escape(report.mod_name),
        generated_at=report.generated_at,
        n_critical=len(report.critical_conflicts),
        n_tenured=len(report.tenured_conflicts),
        n_tangential=len(report.tangential_conflicts),
        n_new=len(report.new_vanilla),
        n_deleted=len(report.deleted_vanilla),
        total_changed=report.total_vanilla_changed,
        version_help=VERSION_HELP_HTML if include_version_help else "",
        filter_bar_critical=build_filter_bar(report.critical_conflicts, "list-critical"),
        filter_bar_tenured=build_filter_bar(report.tenured_conflicts, "list-tenured"),
        filter_bar_tangential=build_filter_bar(report.tangential_conflicts, "list-tangential"),
        filter_bar_new=build_filter_bar(report.new_vanilla, "list-new"),
        critical_items=items_or_empty(report.critical_conflicts, "conflict"),
        tenured_items=items_or_empty(report.tenured_conflicts, "watch"),
        tangential_items=items_or_empty(report.tangential_conflicts, "tangential"),
        new_items=items_or_empty(report.new_vanilla, "new"),
        deleted_items=items_or_empty(report.deleted_vanilla, "deleted"),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

VERSION_HELP_TEXT = """
How to Obtain the Previous Stellaris Version
============================================

Option A — DepotDownloader (recommended, Windows/macOS/Linux):
  1. Download: https://github.com/SteamRE/DepotDownloader/releases
  2. Find the old manifest ID: https://steamdb.info/app/281990/depots/
     → Pick depot 281991 (Windows) or 281992 (Linux/Mac)
     → Select the entry matching your previous patch date → copy Manifest ID
  3. Run:
       DepotDownloader.exe -app 281990 -depot 281991 -manifest <MANIFEST_ID> -dir ./stellaris_old
  4. Use ./stellaris_old as your --old argument.

Option B — steamctl (Python CLI):
  pip install steamctl
  steamctl depot download -a 281990 -d 281991 -m <MANIFEST_ID> --output ./stellaris_old

Option C — Steam beta branch (before updating):
  Before Paradox pushes a new patch, right-click Stellaris in Steam
  → Properties → Betas → select the previous version branch (if available)
  and copy the game files to a safe folder before switching back.

Common Stellaris App/Depot IDs:
  App:        281990
  Depot Win:  281991
  Depot Linux:281992
  Depot Mac:  281993
"""


def parse_args():
    p = argparse.ArgumentParser(
        description="BtR / Binary Helix — Stellaris Patch Compatibility Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--old",   required=False, help="Path to OLD vanilla Stellaris directory")
    p.add_argument("--new",   required=False, help="Path to NEW vanilla Stellaris directory")
    p.add_argument("--mod",   required=False, help="Path to your mod directory")
    p.add_argument("--out",   default="btr_patch_report.html", help="Output HTML file (default: btr_patch_report.html)")
    p.add_argument("--old-label", default=None, help="Label for old version (e.g. 'v3.10')")
    p.add_argument("--new-label", default=None, help="Label for new version (e.g. 'v3.11')")
    p.add_argument("--help-versions", action="store_true", help="Show instructions for downloading old Stellaris versions")
    p.add_argument("--no-version-help", action="store_true", help="Omit version-download instructions from HTML report")
    return p.parse_args()


def main():
    args = parse_args()

    if args.help_versions:
        print(VERSION_HELP_TEXT)
        sys.exit(0)

    if not args.old or not args.new or not args.mod:
        print("ERROR: --old, --new, and --mod are all required.\n")
        print("For version download help: python btr_analyzer.py --help-versions")
        sys.exit(1)

    old_dir = Path(args.old).resolve()
    new_dir = Path(args.new).resolve()
    mod_dir = Path(args.mod).resolve()

    for d, label in [(old_dir, "--old"), (new_dir, "--new"), (mod_dir, "--mod")]:
        if not d.is_dir():
            print(f"ERROR: {label} path does not exist or is not a directory: {d}")
            sys.exit(1)

    old_label = args.old_label or old_dir.name
    new_label = args.new_label or new_dir.name

    # Build output filename from version labels unless --out was explicitly set
    if args.out != "btr_patch_report.html":
        out_path = Path(args.out)
    else:
        def safe_label(s: str) -> str:
            return re.sub(r'[\\/:*?"<>|]', "", s).strip()
        out_path = Path(f"{safe_label(old_label)}-{safe_label(new_label)}.html")

    print(f"\nBtR Stellaris Patch Analyzer")
    print(f"{'='*50}")
    print(f"  OLD vanilla : {old_dir}")
    print(f"  NEW vanilla : {new_dir}")
    print(f"  Mod dir     : {mod_dir}")
    print(f"  Output      : {out_path}")
    print()

    report = analyze(old_dir, new_dir, mod_dir, old_label, new_label)

    print("\nGenerating HTML report …", flush=True)
    html_out = generate_html(report, include_version_help=not args.no_version_help)
    out_path.write_text(html_out, encoding="utf-8")
    print(f"  ✓ Report saved to: {out_path.resolve()}")
    print(f"\nSummary:")
    print(f"  {{len(report.critical_conflicts):4d}}  Critical conflicts  (mod overrides changed this patch)")
    print(f"  {{len(report.tenured_conflicts):4d}}  Tenured conflicts   (mod overrides unchanged vanilla)")
    print(f"  {{len(report.tangential_conflicts):4d}}  Tangential conflicts (vanilla in mod folders, no override)")
    print(f"  {{len(report.new_vanilla):4d}}  New vanilla files   (potential content to adopt)")
    print(f"  {{len(report.deleted_vanilla):4d}}  Deleted vanilla     (may break mod references)")
    print()


if __name__ == "__main__":
    main()
