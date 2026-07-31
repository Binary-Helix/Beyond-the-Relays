# BtR Compatibility Audit — Stellaris 4.0.23 → 4.4.1 "Pegasus" + Nomads

**Date:** 2026-06-17
**Auditor:** Claude Code (static diff-based audit)
**Mod:** Beyond the Relays (`E:\Repositories\btr_skunkworks`), branch `build/dev-build`
**Vanilla baseline used for diffing:** `F:\SteamLibrary\steamapps\common\Stellaris` — **Pegasus v4.4.1 (8e23)**, `modsCompatibilityVersion 4.4`

## Purpose

Work on BtR is resuming after a months-long pause. Stellaris has since shipped four minor
versions — **4.1 Omen, 4.2 Astral Planes, 4.3 Machine Age, 4.4 "Pegasus"** (released
2026-06-15, bundled with the **Nomads** expansion). The mod still declares
`supported_version="v4.0.23"`. This audit identifies **everything that must change** to bring
the mod to full feature parity with 4.4.1.

### Scope decisions (set by the maintainer for this effort)
- **Goal:** full feature parity with 4.4.1, aligned to the *Mass Effect: Beyond the Relays
  Codex 2.0*.
- **Nomads:** **integrate** into ME canon (Arkship / migrant-fleet gameplay mapped onto ME
  factions — e.g. the Quarian Migrant Fleet), not suppress.
- **This deliverable:** the audit only. No code changes have been made.

## Report contents

| File | Covers |
|------|--------|
| `00-overview.md` | This file — context, risk model, methodology |
| `01-blocking-issues.md` | Errors/crashes & removed-feature usage that break on 4.4.1 |
| `02-stale-overrides.md` | Overridden vanilla files frozen at 4.0 that must be re-merged |
| `03-new-systems-parity.md` | New vanilla systems/files the mod has no coverage for |
| `04-nomads-me-integration.md` | Designing Nomads → ME canon; vanilla-origin leak gating |
| `05-remediation-roadmap.md` | Prioritized, phased execution plan + verification |
| `06-phase0-baseline-findings.md` | **Phase 0 run output** — error.log analysis on v4.4.3, confirming B-2/B-3/B-5/B-6/B-7 |

## The core risk: the hard-override model

BtR is a **total conversion that uses hard file overrides and declares NO `replace_path`** in
`descriptor.mod`. In Stellaris, a mod file replaces a vanilla file **only when it shares the
exact relative path + filename**. Everything else loads from vanilla normally.

Verified collision counts vs. vanilla 4.4.1 (`common/`):

- **~129 file collisions under `common/`**, including **100% overrides** of:
  - `pop_jobs/` (11 files), `buildings/` (13), `districts/` (4),
  - `pop_categories/`, `economic_plans/`, `planet_classes/`, `on_actions/`.

**Consequence:** each overridden file is frozen at the 4.0 era. Where vanilla changed that file
across 4.1–4.4, the mod's stale copy **silently shadows the new vanilla content**. The master
`00_on_actions.txt` override is the worst case — it deletes every on_action hook vanilla added
in four versions (Nomads/arkship/contract/Machine-Age events, etc.).

## Methodology

1. Confirmed the live vanilla version and located the install for direct file diffing.
2. Pulled the official 4.4 "Pegasus" modding release notes for removed/renamed tokens.
3. Enumerated mod↔vanilla file collisions and computed per-file line deltas.
4. Grep-verified specific removed/renamed tokens against both trees.
5. Inventoried new vanilla files/directories with no mod counterpart.

## Framing caveat (read before acting on findings)

A vanilla `common/` subdirectory the mod **does not override is not a defect** — vanilla loads
it. There are ~90 such directories (ethics, casus_belli, diplomatic_actions, etc.) that have
existed for years and need no action. **Only two classes of finding are real:**

1. **Stale overrides** — files the mod *does* override that have diverged from 4.4.1 (`02-…`).
2. **New systems** — content/systems added in 4.1–4.4 that the mod must theme or integrate for
   parity + ME canon (`03-…`).

Do not treat the raw "vanilla-only directory" list as a defect list.

## Important limitation

This is a **static diff-based audit**. The authoritative compatibility signal is the in-game
`error.log` produced by running the mod on 4.4.1. A live run (see `05-…` Verification) should
follow and any deltas folded back into these findings.
