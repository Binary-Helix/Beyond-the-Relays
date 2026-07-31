# BtR → Stellaris 4.4.6 "Pegasus" — Updated Compat Audit & Remediation Plan

## Context

Beyond the Relays still targets Stellaris **4.0.23**; the live game is now **v4.4.6** (June audit was vs 4.4.1). The June audit (`COMPAT-AUDIT-4.4-PEGASUS-2026-06-17/`, 7 docs) remains valid — re-verification today confirms **every blocker (B-1…B-7) is still present at identical scale and zero remediation commits exist** (newest branch commit: 2026-06-05). This plan supersedes `05-remediation-roadmap.md` with a fresh verification pass, a more complete override inventory, granular tasks, and an automation-first workflow. btr_studio is **on hold** (user directive 2026-07-31) — all automation is standalone scripts in this repo.

**User decisions (2026-07-31):** scripts live in committed `tools/compat/`; Phase 4 (ME-theming of new vanilla systems) is **deferred** — this plan covers mechanical compat only; fetch vanilla **4.0.23 via Steam betas** for 3-way merges; **commit** the audit folder.

## Fresh verification results (2026-07-31)

**Blockers — all still present:**
- B-1: `descriptor.mod:15` = `v4.0.23`.
- B-2: 136 `promotion`/`demotion` blocks across 9 `common/pop_jobs/*.txt`; `common/pop_categories/03_unemployment.txt` exists; 37 `*_unemployment` refs across 18 files.
- B-3/B-5: `is_capped_by_modifier` ×133 across 8 files (top: `buildings/btr_planet_unique_buildings.txt` 39, `pop_jobs/00_other_jobs.txt` 39, `districts/btr_planetarystations_districts.txt` 35); `inherits_capped_modifiers_from` ×1 in `districts/02_rural_districts.txt`; replacement `shared_capacity_modifier` used 0 times.
- B-6: `common/star_classes/00_star_classes.txt` override intact (8,766 diff lines vs 4.4.6).
- B-7: ~809 planet-scope calls in planetarystations files — 616 of them in `common/scripted_effects/btr_planetarystations_scripted_effects.txt`.
- Dangling refs `turian_hier_origin` / `ap_defender_of_the_galaxy_nomads` / `ap_wanderlust`: already gone from live code. `sc_crisis_binary_1` commented-only. Orphan `gfx/FX/rs_pdxmesh.shader` still present.

**Collision inventory vs 4.4.6** (recomputed): 547 total — `common/` **129** (same count as June, contents drifted), gfx 317, flags 64, interface 22, map 5, sound 3, music 6, events 1, **localisation 0** (all mod loc files are `btr_`-prefixed — purely additive, good).

**New findings the June audit missed** (never listed for re-merge): `scripted_triggers/00_scripted_triggers.txt` (11,032 diff lines — 2nd worst in repo), `policies/00_policies.txt` (9,728), `component_templates/` ×22, `ai_budget/` ×16, `traits/` ×8 (incl. `01_species_traits_habitability` 6,404), `section_templates/` ×8, **`ship_sizes/` ×6** (June audit assumed ship_sizes wasn't overridden — it is, and likely explains the Nomads `starbase_*` reference cascade in the baseline log), `traditions/` ×4, `deposits/` ×3, `ascension_perks/` ×2, plus ~15 singletons (`edicts/01_campaigns`, `strategic_resources`, `random_names`, `agreement_term_values`, …).

**Quick wins found:** 3 overrides are functionally identical to vanilla (whitespace-only) → delete: `pop_jobs/10_paragon_fake_jobs.txt`, `pop_jobs/14_wilderness_jobs.txt`, `traditions/00_logistics.txt`.

**Baseline gap:** the newest error.log (Jul 5, v4.4.4, 2,641 lines) was run with the **btr_devbuild Workshop copy** (`remote_file_id 2969357504`), not the repo. The `mod/btr_skunkworks` → repo junction is verified in place but has **never been launched** — a faithful repo baseline is still outstanding.

---

## Phase 0 — Baseline & tooling (do first; ~1–2 sessions)

| # | Task | Automation |
|---|------|-----------|
| 0.1 | Commit `COMPAT-AUDIT-4.4-PEGASUS-2026-06-17/` (+ `BTR_STUDIO.md` pointer if desired) to the branch | manual, trivial |
| 0.2 | Create `tools/compat/collisions.py` — enumerate mod↔vanilla path collisions + per-file diff stats (whitespace-normalized) vs configurable vanilla path; emits markdown/CSV. Re-run after every vanilla patch | **full script** |
| 0.3 | Create `tools/compat/errorlog_report.py` — parse `error.log` → (subsystem, token/signature, file, count) table; `--diff old new` prints **net-new errors**. This is the exit gate for every phase | **full script** |
| 0.4 | Create `tools/compat/token_scan.py` — burndown scanner for deprecated tokens (`promotion`, `demotion`, `is_capped_by_modifier`, `inherits_capped_modifiers_from`, `*_unemployment`, planet-scope-in-colony patterns). Zero counts = B-series done | **full script** |
| 0.5 | **Capture faithful repo baseline:** launch 4.4.6 with only `btr_skunkworks` enabled (junction → repo), let it crash if it crashes, save `error.log` + report as `COMPAT-AUDIT…/07-repo-baseline-4.4.6.md` | script 0.3 |
| 0.6 | **Fetch vanilla 4.0.23** via Steam → Stellaris → Properties → Betas (old-version branches) into a separate dir (e.g. `E:\tmp\stellaris-4.0.23`); copy the 129 colliding files as 3-way merge bases into `tools/compat/base-4.0/`; then restore Steam to current. Fallback: nearest 4.0.x branch; last resort 2-way review | manual download + script copy |
| 0.7 | Regenerate the stale-overrides table vs 4.4.6 (script 0.2) → commit as `02b-stale-overrides-4.4.6.md` (full 129-file table, grouped, with divergence) | script 0.2 |

## Phase 1 — Boot blockers (goal: reach main menu + new game, B-series log-clean)

| # | Task | Automation |
|---|------|-----------|
| 1.1 | Delete the 3 functionally-identical overrides (quick win, shrinks surface) | trivial |
| 1.2 | Bump `descriptor.mod` `supported_version` → `v4.4.*` | trivial |
| 1.3 | Write + run `tools/compat/strip_blocks.py` — brace-balanced removal of the 136 `promotion`/`demotion` blocks in 9 pop_jobs files; review the diff | **script + review** |
| 1.4 | Remove `pop_categories/03_unemployment.txt`; fix the 37 `*_unemployment` references across 18 files (scanner lists sites; each edited deliberately — some migrate to 4.4's `forced_integration` model) | semi-auto |
| 1.5 | Convert `is_capped_by_modifier` ×133 + `inherits_capped_modifiers_from` ×1 → `shared_capacity_modifier`: first verify the 4.4 syntax on one vanilla example per pattern (vanilla `districts/`, `buildings/`), then scripted rename + spot review | semi-auto |
| 1.6 | `star_classes/00_star_classes.txt`: 3-way merge vs 4.4.6 stellar rework; if BtR's changes are additive, move to a `btr_star_classes.txt` and delete the override | 3-way merge harness (2.0) |
| 1.7 | **Colony/Carrier scope fix (B-7):** one design pass to define the rewrite patterns (planet→colony scope, `has_planet_flag` on colony scope, etc.) against vanilla 4.4 usage, then apply across the ~809 sites — 616 are in a single file (`btr_planetarystations_scripted_effects.txt`), so this is one focused file + 10 small ones. Verify via `trigger.cpp`/`event.cpp` counts in the log | design pass + scripted replace |
| 1.8 | Delete orphan `gfx/FX/rs_pdxmesh.shader`. If load still crashes after B-fixes, run the gfx isolation test from `06-…` (temporarily pull overridden vanilla `.asset` files → relaunch → bisect) | manual, small |
| 1.9 | **Exit gate:** relaunch → `errorlog_report.py --diff` vs 0.5 baseline; require zero B-series signatures and successful new game with a BtR empire | script 0.3 |

## Phase 2 — De-override & master re-merges (highest blast radius)

**Standard per-file workflow (build once as `tools/compat/remerge.py`, reuse for all of Phases 2–3):**
`git merge-file` style 3-way merge: base = vanilla 4.0.23 copy, ours = mod file, theirs = vanilla 4.4.6 → auto-merges everything non-conflicting; only true conflicts (vanilla changed a block BtR also edited) need human/Claude resolution. Normalize CRLF/BOM before diffing (June audit hit false 100%-diffs from line endings).

**De-override rule:** wherever BtR's delta vs 4.0.23 is purely *additive* (new entries only), move the additions to a mod-only `btr_*.txt` in the same dir and delete the override entirely — permanently ends the re-merge treadmill for that file. `on_actions` is explicitly safe for this (same-key on_action blocks merge across files).

| # | Task (in order) | Why |
|---|------|-----|
| 2.1 | `on_actions/00_on_actions.txt` (11,507 diff lines) → de-override into `btr_on_actions.txt` | restores every 4.1–4.4 vanilla hook |
| 2.2 | `scripted_triggers/00_scripted_triggers.txt` (11,032) | **new finding** — huge, load-bearing |
| 2.3 | `policies/00_policies.txt` (9,728) | **new finding** |
| 2.4 | `planet_classes/00_planet_classes.txt` | pairs with 1.6 stellar rework |
| 2.5 | `governments/councilors/00_councilors.txt` | 4.x councilor changes |
| 2.6 | `ship_sizes/` ×6 + `section_templates/` ×8 | **new finding**; suspected cause of Nomads `starbase_*` cascade — verify cascade disappears in log after |
| 2.7 | Exit gate: log diff net-new = 0 | script 0.3 |

## Phase 3 — Batch re-merge remaining overrides (~100 files, grouped; parallelizable)

Each row = one independent task using the same `remerge.py` workflow + log gate. Order by player impact:

| Batch | Files | Note |
|-------|-------|------|
| pop_jobs | 11 | promotion/demotion already stripped in 1.3; this picks up new 4.4 job fields |
| buildings | 13 | all behind vanilla; reconcile capital-shelter `inline_script` vs vanilla `job_dystopian_enforcer_add` |
| districts | 4 | includes the 1.5 conversion; pick up `convert_to district_ark_generator` |
| pop_categories + economic_plans | 3 | small but strata/living-standard reworked in 4.x |
| traits | 8 | `01_species_traits_habitability` is 6,404 diff lines |
| component_templates | 22 | mostly weapons/utilities; many near-identical — de-override candidates |
| ai_budget | 16 | small files; likely bulk-mergeable |
| traditions + ascension_perks | 6 | |
| deposits + armies + anomalies | 9 | 3 vanilla anomaly-category files |
| misc singletons | ~15 | `edicts/01_campaigns`, `strategic_resources`, `random_names`, `agreement_term_values`, `artifact_actions`, `economic_categories`, `job_tags`, `country_customization`, `gamesetup_settings`, `tradable_actions`, `technology/00_ancient_relics_tech`, `scripted_effects/cosmic_storms_scripted_effects`, inline_scripts ×4, `scripted_triggers/01_…_buildings` |
| events/ ×1, map/ ×5, interface/ ×22 | 28 | identify + re-merge; interface `.gui` stale overrides can hide new 4.4 UI widgets |
| gfx asset suspects | ~20 of 317 | only the vanilla-overriding `.asset` entity/particle files flagged in `06-…` (`_planetary_entities.asset` 2,733 diff lines, `_star_entities.asset`, star_lights, 15 ship particle assets). The other ~297 gfx collisions are intentional TC reskins — leave unless log/crash implicates them |

## Phase 4 — DEFERRED: new-systems ME theming

Not in this plan (user decision). After Phases 0–3 land, vanilla Nomads/Machine Age/Astral/Storms/Grand Archive content will load un-themed — that's the Phase 4 design effort (needs *Codex 2.0* access; see `03-…`/`04-…`). One caveat to carry forward: vanilla nomadic origins/civics will be visible in empire creation until gated — acceptable for a dev build, must be resolved before release.

## Phase 5 — Localisation sweep

| # | Task | Automation |
|---|------|-----------|
| 5.1 | `tools/compat/loc_check.py` — (a) keys referenced in `common/`+`events/` missing from `localisation/english/`; (b) English keys missing stubs in the other 7 languages | **full script** |
| 5.2 | Fix everything it reports (stub non-English with English values per CLAUDE.md) | semi-auto |

## Phase 6 — Validation & PR

- Full fresh-save playtest with a representative BtR empire; error.log clean vs Phase 0 baseline (net-new = 0, ideally far below the 2,641-line devbuild log).
- PR per `.github/pull_request_template.md`; save-compat flag = **new game required** (pop/job/category changes guarantee it).

## Automation summary (what runs itself vs what needs judgment)

- **Fully scripted, re-runnable (`tools/compat/`):** collision inventory (0.2), error.log normalize+diff gate (0.3), deprecated-token burndown (0.4), promotion/demotion block stripper (1.3), 3-way merge harness (2.0), loc checkers (5.1), CRLF/BOM normalizer.
- **Semi-automated (script finds/applies, Claude or human verifies):** `is_capped_by_modifier` conversion, `*_unemployment` ref fixes, colony-scope rewrites, merge-conflict resolution.
- **Claude fan-out (optional, later):** Phase 3 batches are independent per-file tasks — ideal for parallel subagents in future sessions if the user opts in.
- **Judgment-only:** de-override decisions, B-7 scope-pattern design, gfx crash bisect, Phase 4 canon design.

## Verification (every phase)

1. Junction `Documents/…/mod/btr_skunkworks` → repo (already in place; re-create if launcher repairs it).
2. Launch 4.4.6, only BtR enabled; new game with a BtR empire when boot succeeds.
3. `tools/compat/errorlog_report.py --diff baseline current` → **net-new errors must be 0** to exit a phase.
4. `token_scan.py` counts must be at/under the phase's target (0 after Phase 1).
5. Spot checks: empire creator, jobs/buildings/districts menus, pop employment.
