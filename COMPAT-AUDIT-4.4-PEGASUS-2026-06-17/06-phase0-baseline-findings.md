# 06 — Phase 0 Baseline Run Findings

**Run date:** 2026-06-21
**Game version:** **Pegasus v4.4.3** (auto-updated past 4.4.1; still 4.4.x — audit holds)
**Enabled mods:** only `mod/btr_skunkworks.mod` (clean isolation — `dlc_load.json` confirms)
**Log:** `…/Documents/Paradox Interactive/Stellaris/logs/error.log` — **2,215 lines**

## ⚠️ Deployment caveat (important)

The launched mod (`…/Stellaris/mod/btr_skunkworks`, a **real copy**, not a symlink) is an
**older Steam-Workshop-published build** (`remote_file_id 3556652704`), **not** the current
`feature/compat/stellaris-4.4-pegasus` / `build/dev-build` repo. A `diff -rq` shows **294
differing files under `common/`** plus structural differences (e.g. repo uses
`solar_system_initializers/canon/btr_attican_traverse/` subfolders; the deployed copy has flat
`00_attican_traverse_initializers.txt`).

**Therefore:** findings below are split into **✅ repo-confirmed** (the offending construct also
exists in our branch — verified by grep/checksum) and **🔁 re-verify** (deployed-only or
uncertain until we run the actual repo). For a faithful baseline, repoint the deployment at the
repo and re-run (see "Next step").

## Error volume by engine subsystem (top)

| Count | Subsystem | Interpretation |
|------:|-----------|----------------|
| 505 | `persistent.cpp` | parse/DB load failures (the token errors below funnel here) |
| 143 | `economic_unit_template.cpp` | economy/job templates — largely downstream of B-2/B-5 |
| 119 | `event.cpp` | event scope/validation |
| 102 | `eventpicture.cpp` | missing event pictures/sounds (content/assets) |
| 73 / 69 / 45 | audio / sprite / portraits | missing asset references |
| 61 | `trigger.cpp` | wrong-scope triggers (B-7) |
| 37 | `job_type.cpp` | job definitions (B-2) |

## ✅ Repo-confirmed findings

| ID | Finding | Log signature (count) | Repo evidence |
|----|---------|-----------------------|---------------|
| **B-2** | `promotion`/`demotion` blocks removed in 4.4 | `Unexpected token: promotion` ×111, `…: demotion` ×25 | 136 blocks across 9 `pop_jobs/*.txt` |
| **B-5** | `is_capped_by_modifier` deprecated | `Unexpected token: is_capped_by_modifier` ×25 | used in 8+ files (planetary-stations + 5 pop_jobs) |
| **B-3** | `inherits_capped_modifiers_from` deprecated | (1) | `districts/02_rural_districts.txt:692` |
| **B-6** | `star_classes` override stale vs 4.4 stellar rework | `Unexpected token: stars` ×23, `name` ×23, `entropy_crystals` ×14, `random_list already exists` ×22 | repo overrides `common/star_classes/00_star_classes.txt`, contains those tokens |
| **B-7** | `planet`→`colony` scope split (Carrier/Colony) | `Current Scope: colony` (supported: planet) ×64; `Wrong scope … has_planet_flag` | repo files: `btr_planetarystations_zones.txt` (22), planetary-station buildings/megastructure, 5 overridden vanilla building files |

These five are now documented as blockers **B-2/B-3/B-5/B-6/B-7** in `01-blocking-issues.md`.

### Note on the override thesis
B-6 and B-7 directly demonstrate `00-overview.md`'s core risk: stale `00_*` overrides
(`star_classes`) and 4.0-era scope assumptions (planetary stations) break on 4.4. The economy
(`economic_unit_template.cpp` ×143) and `job_type.cpp` errors are largely **downstream** of B-2
(once jobs fail to parse, the economy templates that reference them fail too) — expect most of
these to clear once B-2/B-5 are fixed.

## 🔁 Findings to re-verify on a repo baseline

| Finding | Log signature (count) | Why uncertain |
|---------|-----------------------|---------------|
| `btr_anomalies.txt` syntax errors | `…btr_anomalies.txt near line N` ×133 (within the 262 `Unexpected token: =` cluster) | repo's `btr_anomalies.txt` **differs** from the deployed copy |
| Nomads `starbase_*` reference cascade | `Failed to read key reference starbase_waystations_modules` ×33; `starbase_arkship_upgrades` ×26/25/20; `starbase_arkships` ×9 | repo has **0** `starbase_modules`/`starbase_buildings` overrides — may be deployed-copy-only or a cascade from the repo's 9 `ship_sizes` overrides shadowing nomad ship keys |
| `ap_defender_of_the_galaxy_nomads` resolution ref | `…resolutions/…nemesis.txt` ×16 | repo overrides 1 `resolutions` file; confirm it's the shadowing cause |
| Missing event pictures/sounds | `btr_precursor_collective.N … non-existent event picture show_sound` / `missing a sound` ×11 each; `eventpicture.cpp` ×102 | likely real but may be pre-existing asset gaps, not 4.4-specific |

## Cross-reference to the audit

- B-2/B-3/B-5/B-6/B-7 → `01-blocking-issues.md`
- Carrier/Colony scope (B-7) → `03-new-systems-parity.md` §E
- Nomads `starbase_*`/`ship_sizes` shadowing → validates `02-stale-overrides.md` + `03-…` §A
  (the override model deleting new vanilla nomad content)

## Load crash (both runs)

Both the Jun 21 (13:37) and Jun 22 (01:55) launches **crashed during load** —
`EXCEPTION_ACCESS_VIOLATION (C0000005)` in PHYSFS, at the **end of the deferred-database read
phase** (crash timestamp matches the last deferred-read errors). So the "baseline" `error.log`
is from a **crashed load**, not a completed game start. The errors are still valid (they are
parse/link failures emitted before the crash), but the game never reached the main menu/galaxy.

**Cause:** not a single corrupt asset — it is the accumulated 4-version drift. Deferred
references that no longer resolve (e.g. removed origin key `turian_hier_origin`, Nomads
`sc_crisis_binary_1/2`, `ap_defender_of_the_galaxy_nomads`, `ap_wanderlust`) leave dangling
pointers the engine dereferences during final linking. A 4.0-era total conversion **crashing on
load against 4.4.3 is the expected outcome**; a clean load is not achievable until the blockers
(B-2/B-5/B-6/B-7 and the dangling deferred refs) are fixed. **The crash is therefore a symptom,
not a separate bug to minidump-dive.**

Non-fatal but notable load errors also seen: missing portrait `.dds` textures
(`gfx/models/portraits/...`) and missing sound effects — asset gaps to revisit, lower priority
than the script blockers.

## Deployment fixed — next run tests the repo

The launcher (v2) **rewrote `btr_skunkworks.mod` from its sqlite cache**, reverting the `path=`
edit, so both runs loaded the older published Workshop copy, not our branch. Fixed with a
**directory junction** that the launcher cannot revert:

- `…/Stellaris/mod/btr_skunkworks` → **junction** → `E:\Repositories\btr_skunkworks`
- the published copy is preserved at `…/mod/btr_skunkworks_published_bak`
- verified: files that differed (`04_manufacturing_buildings.txt`, `btr_anomalies.txt`,
  `descriptor.mod`) now resolve to the **repo** version through the junction.

**To capture the faithful repo baseline:**
1. Launch v4.4.3 with only **btr_skunkworks** enabled. *(It will very likely still crash on
   load — that's fine; the `error.log` is written before the crash.)*
2. Exit / let it crash.
3. I read `logs/error.log`, diff against the published run, and resolve the 🔁 items
   (`btr_anomalies.txt`, the Nomads `starbase_*` cascade) against our actual code.

> If the launcher ever "repairs"/re-downloads the mod and breaks the junction, re-create it
> (or remove `remote_file_id` and the Workshop subscription so it's treated as purely local).

## gfx / shader / particle review (post-update crash hypothesis)

Reviewed per the standard "post-patch crashes come from stale `gfx` shader/particle files" rule.

**Overridden engine shaders — `gfx/FX/` (structurally compatible, low crash risk):**
| File | Real diff vs 4.4.3 (line-endings normalized) | Nature |
|------|-----|--------|
| `border.shader` | 8 lines | cosmetic: Primary/Secondary blend swap |
| `pdxmesh.shader` | 26 lines | cosmetic: env-reflections disabled ("black space" look); **no** missing ConstantBuffer/technique/vertex-struct — structurally current |
| `restorescene.shader` | 12 lines | cosmetic: lens-flare brightness tweak |
| `rs_pdxmesh.shader` | — | **removed by vanilla 4.4.3** (orphan); **not referenced** anywhere in mod gfx → dead file, safe to delete, not the crash |

The CRLF/LF artifact initially made these look 100% changed; normalized, they are ~99% identical
to 4.4.3 with only HLSL-body tweaks. Shaders also compile during **graphics-init (01:53:50, which
succeeded)** — the crash is later (01:55:12) during entity/database load — so the shaders are an
unlikely cause.

**More suspect, given crash timing — 4.0-era overridden vanilla `.asset` entity/particle files:**
- `gfx/models/planets/_planetary_entities.asset` — overrides vanilla, **2,733** differing lines
- `gfx/models/planets/_star_entities.asset` — 46 differing lines (intersects the 4.4 stellar-
  classification rework / B-6)
- `gfx/lights/star_lights.asset` (4), `gfx/models/galaxy_map/_galaxy_map_objects.asset` (24)
- **15 overridden vanilla ship/station particle assets** (`gfx/particles/ships/*explosion*.asset`,
  `*_burn_effect.asset`, …)

These replace vanilla entity/particle definitions wholesale; if any reference an attribute/effect
changed in 4.4, the native entity loader can AV during the asset-load phase (matching the crash
timing). **However**, the crash stack is symbol-stripped (the "PHYSFS_*" frames are just the
nearest exported symbol, offsets in the MB range), so logs **cannot** confirm gfx-vs-script.

**Decisive test (isolation):** temporarily pull the mod's overridden-vanilla gfx files (so the
game falls back to vanilla gfx) and relaunch.
- Still crashes at ~the same point → gfx exonerated; cause is the script deferred-refs
  (B-2/B-6 + dangling origin/Nomads references).
- Loads / crashes differently → gfx confirmed; bisect down to the offending asset.
