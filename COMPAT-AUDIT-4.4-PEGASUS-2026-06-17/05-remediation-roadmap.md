# 05 — Remediation Roadmap

Phased plan to reach full 4.4.1 parity + Nomads-ME integration. Each phase ends with a deploy +
`error.log` check (see Verification). Effort is rough order-of-magnitude (S/M/L/XL).

## Phase 0 — Baseline & safety (S)
- Branch `feature/compat/stellaris-4.4-pegasus` off `build/dev-build`.
- Deploy current mod against 4.4.1 **as-is** and capture a baseline `error.log` — this is the
  ground-truth defect list to validate this audit against.
- Snapshot vanilla 4.4.1 copies of every overridden file for diffing.

## Phase 1 — Boot & clean the log (S–M) — `01-blocking-issues.md`
- **B-1:** bump `descriptor.mod` → `v4.4.1`.
- **B-2:** remove obsolete unemployment categories (`pop_categories/03_unemployment.txt`); strip
  `promotion`/`demotion` blocks from the 9 `pop_jobs/*.txt`; migrate intended demotion to
  `forced_integration` on species traits; purge dangling references to `*_unemployment` keys.
- **B-3:** convert `inherits_capped_modifiers_from` (`districts/02_rural_districts.txt:692`) to
  `shared_capacity_modifier`.
- **B-4:** grep-confirm no renamed-token regressions.
- **Exit criteria:** mod boots; new-game start with a BtR empire; `error.log` clean of the B-series
  issues.

## Phase 2 — Re-merge stale master files (M–L) — `02-stale-overrides.md`
- Re-merge in priority order: `on_actions/00_on_actions.txt` →
  `planet_classes/00_planet_classes.txt` → `governments/councilors/00_councilors.txt`.
- **Strategic refactor:** migrate additive BtR edits out of vanilla `00_*` masters into mod-only
  `btr_*.txt` files where possible and stop overriding the master (kills the future re-merge
  treadmill). `00_on_actions.txt` first.
- **Exit criteria:** new 4.1–4.4 vanilla on_actions/planet-classes/councilors present; no
  duplicate-definition errors.

## Phase 3 — Re-merge content overrides (L) — `02-stale-overrides.md`
- `buildings/` (13, all behind vanilla), `pop_jobs/` (11), `districts/` (4),
  `pop_categories/` (2), `economic_plans/01_base.txt`.
- Fold the B-2 promotion/demotion strip into the pop_jobs pass.
- Reconcile divergent patterns (e.g. capital-shelter `inline_script` vs vanilla
  `job_dystopian_enforcer_add`).
- **Exit criteria:** content menus (buildings/districts/jobs) populate correctly; economy not
  visibly broken; log clean for these files.

## Phase 4 — Integrate new systems per Codex (XL) — `03-…`, `04-…`
- **Nomads → ME (priority):** arkship districts/zones/buildings/jobs/megastructures/modules,
  contracts (`missions`), nomad situations; gate or reskin leaking vanilla nomadic origins/civics;
  wire to the existing Migrant Fleet chain; audit planet→Carrier/Colony scope in BtR events.
- **Machine Age, Astral Planes, Cosmic Storms, Grand Archive, Biogenesis, Shroud, Wilderness:**
  decide per system — reskin to ME or gate off; implement the chosen path.
- **Blocked on Codex access** for canon mappings (`04-…`).
- **Exit criteria:** new systems either present as ME-themed content or intentionally gated; no
  raw-vanilla content leaking into the curated ME experience.

## Phase 5 — Localisation sweep (M)
- Add English keys for all new/changed content; stub across the 8 languages so no raw keys show.
- Pick up any vanilla loc-key renames touched by re-merges.

## Phase 6 — Validation & PR (M)
- Full verification pass (below); fresh-save and existing-save tests per PR template.
- Complete `.github/pull_request_template.md` checklist; flag save-game compatibility (this is a
  new-game-required change given the pop/job/origin scope).

## Suggested sequencing & parallelism
- Phases 1→2→3 are sequential (each rests on a clean prior log).
- Within Phase 3, the 13 buildings / 11 pop_jobs / 4 districts re-merges are independent and can
  be split among contributors.
- Phase 4 sub-systems are independent once Phase 3 lands and the Codex is available.

## Verification (applies after each phase)

1. **Deploy:** point a `.mod` in
   `%USERPROFILE%\Documents\Paradox Interactive\Stellaris\mod\` at the repo (or symlink), with
   `supported_version` updated; enable only BtR in the launcher on 4.4.1.
2. **Run:** launch 4.4.1; start a new game with a representative BtR empire on the canon map.
3. **Logs:** review `Documents\Paradox Interactive\Stellaris\logs\error.log` and `setup.log`;
   compare against the Phase 0 baseline — net-new errors must be zero.
4. **Spot-check:** empire creator (no unintended leaked origins), pop employment (no broken
   unemployment categories), building/district/job menus, and that targeted new systems behave
   or are gated.
5. **Save compat:** test a fresh save always; test an existing save where the change could be
   backward-compatible. Record results in the PR.
6. Fold any `error.log` deltas back into `01`/`02`/`03`.

## Known dependencies / risks
- **Codex access** blocks Phase 4 canon mappings (`04-…`).
- The pop/job/unemployment and origin changes almost certainly make this **new-game-required**;
  communicate to users.
- This audit is static; the Phase 0 baseline `error.log` is the real source of truth and may
  surface issues not visible by diffing (e.g. runtime scope errors from the Carrier/Colony split).
