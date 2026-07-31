# 02 — Stale Overrides (re-merge against 4.4.1)

Every file below is a **hard override** of a vanilla file that has since diverged. Each must be
re-merged: **take the vanilla 4.4.1 file as the new base and re-apply BtR's edits on top**, then
re-test. The line delta is a divergence signal, not a fix spec — re-merge regardless of sign.

> **Reading the delta:** `delta = mod_lines − vanilla_lines`.
> - **Negative** → vanilla grew (new modifiers/mechanics the mod's copy lacks).
> - **Positive** → usually BtR additions, but for `pop_jobs` it is *partly* because vanilla
>   *removed* the promotion/demotion blocks (so vanilla shrank). Don't read positive as "mod is
>   ahead."

## Master files (highest blast radius — do these first)

| File | mod | van | delta | Note |
|------|-----|-----|-------|------|
| `common/on_actions/00_on_actions.txt` | 5599 | 5901 | **−302** | **Top priority.** Overriding the master on_actions file with a 4.0 copy deletes every on_action hook added in 4.1–4.4 (Nomads/arkship/contract events, Machine Age, `on_system_locked_ship_killed`, `on_leaving_system_fleet`, `on_megastructure_build_start`, etc.). Re-merge BtR's custom hooks onto vanilla 4.4.1 — or better, **move BtR additions into the mod-only `btr_on_actions.txt` and stop overriding `00_on_actions.txt` entirely** if feasible. |
| `common/planet_classes/00_planet_classes.txt` | 1566 | 1847 | **−281** | Vanilla added planet/star classes and fields. Re-merge; confirm BtR's mod-only class files (`btr_stellar_classes.txt`, `btr_*_planet_classes.txt`) still align. |
| `common/governments/councilors/00_councilors.txt` | 1693 | 1875 | **−182** | New/changed councilor definitions (Tradition Swap `unlocks_agenda`, ethics `triggered_country_modifier`). |

## Buildings (13 overrides — all negative, vanilla grew)

| File | mod | van | delta |
|------|-----|-----|-------|
| `buildings/14_branch_office_buildings.txt` | 4331 | 4690 | **−359** |
| `buildings/03_resource_buildings.txt` | 1763 | 1957 | **−194** |
| `buildings/15_overlord_holdings.txt` | 2250 | 2360 | −110 |
| `buildings/05_research_buildings.txt` | 1861 | 1953 | −92 |
| `buildings/12_event_buildings.txt` | 839 | 900 | −61 |
| `buildings/07_amenity_buildings.txt` | 1414 | 1462 | −48 |
| `buildings/00_capital_buildings.txt` | 2018 | 2059 | −41 |
| `buildings/10_deposit_buildings.txt` | 422 | 459 | −37 |
| `buildings/02_government_buildings.txt` | 1460 | 1494 | −34 |
| `buildings/08_unity_buildings.txt` | 3914 | 3942 | −28 |
| `buildings/06_trade_buildings.txt` | 275 | 297 | −22 |
| `buildings/09_army_buildings.txt` | 372 | 394 | −22 |
| `buildings/04_manufacturing_buildings.txt` | 1661 | 1680 | −19 |

Branch-office buildings also intersect with the renamed branch-office influence defines (see
`01-…` B-4). Capital buildings: vanilla `building_colony_shelter` now adds
`job_dystopian_enforcer_add` under `civic_dystopian_society`; the mod handles this via an
`inline_script` instead — reconcile.

## Pop jobs (11 overrides — positive deltas inflated by removed promotion/demotion)

| File | mod | van | delta |
|------|-----|-----|-------|
| `pop_jobs/06_event_jobs.txt` | 3044 | 2441 | +603 |
| `pop_jobs/00_other_jobs.txt` | 2524 | 2017 | +507 |
| `pop_jobs/04_gestalt_jobs.txt` | 3349 | 2914 | +435 |
| `pop_jobs/14_grand_archive_jobs.txt` | 789 | 404 | +385 |
| `pop_jobs/02_specialist_jobs.txt` | 3906 | 3552 | +354 |
| `pop_jobs/13_machine_age_jobs.txt` | 1190 | 898 | +292 |
| `pop_jobs/03_worker_jobs.txt` | 1415 | 1178 | +237 |
| `pop_jobs/01_ruler_jobs.txt` | 782 | 763 | +19 |
| `pop_jobs/15_strange_worlds_jobs.txt` | 265 | 205 | +60 |
| `pop_jobs/10_paragon_fake_jobs.txt` | 131 | 131 | 0 |
| `pop_jobs/14_wilderness_jobs.txt` | 2 | 2 | 0 |

Re-merge must strip the `promotion`/`demotion` blocks (B-2) and pick up new vanilla job fields
and the 4.4 job-automation/turnover changes. Treat `13_machine_age_jobs` and
`14_grand_archive_jobs` as both stale **and** DLC-content overrides.

## Districts (4 overrides — positive, includes BtR custom + zone refs)

| File | mod | van | delta |
|------|-----|-----|-------|
| `districts/02_rural_districts.txt` | 856 | 703 | +153 |
| `districts/03_habitat_districts.txt` | 325 | 279 | +46 |
| `districts/01_arcology_districts.txt` | 477 | 433 | +44 |
| `districts/00_urban_districts.txt` | 2132 | 2112 | +20 |

`02_rural_districts.txt` carries the deprecated `inherits_capped_modifiers_from` (B-3) and is
missing the vanilla `convert_to` target `district_ark_generator` (Nomads). Vanilla also added new
district files the mod lacks entirely — see `03-…` (`07_ark_districts.txt`,
`05_wilderness_districts.txt`, `06_swap_districts.txt`, `00_special_districts.txt`,
`04_ringworld_districts.txt`).

## Pop categories (2 overrides, small deltas) + economic plans

| File | mod | van | delta |
|------|-----|-----|-------|
| `pop_categories/02_other_categories.txt` | 761 | 750 | +11 |
| `pop_categories/00_social_classes.txt` | 219 | 217 | +2 |
| `economic_plans/01_base.txt` | 9 | 9 | 0 (verify content, not just length) |

Equal/near-equal line counts still require a content diff — 4.x reworked living-standard and
strata modifiers.

## Recommended re-merge workflow (per file)

1. `diff` the BtR override against vanilla 4.4.1 to isolate BtR's intentional edits.
2. Start from the **vanilla 4.4.1 file** as the new base.
3. Re-apply only BtR's intentional edits (ME content, balance), dropping anything that merely
   duplicated old vanilla.
4. For `pop_jobs`, also strip promotion/demotion (B-2).
5. Re-test in-game; confirm no new `error.log` entries for that file.

> **Strategic recommendation:** wherever BtR's edits to a `00_*` master file are additive (new
> entries, not edits to vanilla entries), migrate them into a **mod-only `btr_*.txt`** file in the
> same directory and **stop overriding the vanilla master**. This permanently eliminates the
> re-merge treadmill for that file on future patches. `00_on_actions.txt` is the prime candidate.
