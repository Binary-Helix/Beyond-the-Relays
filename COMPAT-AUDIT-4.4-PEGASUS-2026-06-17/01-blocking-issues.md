# 01 — Blocking Issues (error-log level)

These are confirmed breakages or uses of removed/renamed engine features. They should produce
`error.log` entries or broken mechanics on 4.4.1 and must be fixed first.

---

## B-1 — Outdated `supported_version` (cosmetic but mandatory)

- **File:** `descriptor.mod:15` (and the deployed `.mod` copy in the Stellaris mod dir)
- **Current:** `supported_version="v4.0.23"`
- **Fix:** `supported_version="v4.4.1"` (or `"v4.4.*"`).
- **Impact:** launcher flags the mod as "out of date / may not work." Does not by itself break
  anything, but must be bumped once compatibility work lands.

---

## B-2 — Unemployment tier removed in 4.4 (HIGH — mechanic-breaking)

4.4 **removed the intermediate unemployment job types and pop categories**
(`ruler_unemployment`, `specialist_unemployment`, `worker_unemployment`,
`complex_drone_unemployment`, `simple_drone_unemployment`, `slave_unemployment2`) and **removed
the `promotion`/`demotion` blocks from pop-job definitions**. Nascent/demotion behavior is now
handled by `forced_integration` on species traits (`integration_rate`, `minimum_colony_age`).

**Verified in this codebase:**

- `common/pop_categories/03_unemployment.txt` — still defines `ruler_unemployment`,
  `specialist_unemployment`, `worker_unemployment` (273 lines). Vanilla 4.4.1 defines **none of
  these** (grep of vanilla `common/pop_categories/` returns zero matches). This file is mod-only
  now (no vanilla collision) and references obsolete categories.
- **136 `promotion`/`demotion` blocks across 9 `pop_jobs/*.txt` files:**

  | File | promotion/demotion blocks |
  |------|--------------------------|
  | `pop_jobs/06_event_jobs.txt` | 31 |
  | `pop_jobs/02_specialist_jobs.txt` | 24 |
  | `pop_jobs/00_other_jobs.txt` | 23 |
  | `pop_jobs/04_gestalt_jobs.txt` | 19 |
  | `pop_jobs/13_machine_age_jobs.txt` | 12 |
  | `pop_jobs/03_worker_jobs.txt` | 10 |
  | `pop_jobs/14_grand_archive_jobs.txt` | 7 |
  | `pop_jobs/15_strange_worlds_jobs.txt` | 6 |
  | `pop_jobs/01_ruler_jobs.txt` | 4 |

- **Fix:** Delete `03_unemployment.txt`'s obsolete categories (or the file, if it adds nothing
  else), strip the `promotion`/`demotion` blocks from the job definitions during the pop_jobs
  re-merge (see `02-…`), and migrate any intended demotion behavior to `forced_integration` on
  the relevant species traits. Also audit references to the removed category keys
  (`*_unemployment`) elsewhere (modifiers, triggers, localisation).
- **Note:** A first-pass explorer suggested *adding* an `is_unemployment_job` flag to these
  categories. That is **incorrect** — the official 4.4 notes say the categories were removed.
  Do not add the flag; remove the categories.

---

## B-3 — Deprecated `inherits_capped_modifiers_from` (MEDIUM)

- **File:** `common/districts/02_rural_districts.txt:692`
  → `inherits_capped_modifiers_from = district_mining`
- **4.4 change:** `inherits_capped_modifiers_from` was replaced by the
  `shared_capacity_modifier` pool mechanism.
- **Fix:** convert to the `shared_capacity_modifier` pool model (compare against vanilla 4.4.1
  `02_rural_districts.txt` for the new pattern) during the districts re-merge.

---

## B-4 — Other renamed tokens to re-verify after each re-merge

Grep of the current tree found **no** usage of the following 4.4-renamed tokens — but the
overridden master files are stale, so re-check after merging vanilla content in:

- `is_moving` → `is_system_locked` (negated) — **not currently used**.
- `is_authority = auth_corporate` → `is_megacorp = yes` — **not currently used**.
- `BRANCH_OFFICE_COST_INCREASE_MIN_RANGE` / `BRANCH_OFFICE_COST_INCREASE_SCALE` →
  `BRANCH_OFFICE_INFLUENCE_COST_BASE` / `_INCREASE_SCALE` / `_MAX_COST` — **not currently used**,
  but `buildings/14_branch_office_buildings.txt` is stale (−359 lines vs vanilla) and must be
  re-merged carefully.
- Removed defines `AI_RESETTLE_FROM_LOW_HABITABILITY_THRESHOLD`,
  `AI_RESETTLE_TO_HIGH_HABITABILITY_THRESHOLD` — confirm not referenced in any mod `defines`/AI
  override.

---

## B-5 — Deprecated `is_capped_by_modifier` (HIGH — confirmed in baseline log)

The Phase 0 baseline run (`06-phase0-baseline-findings.md`) produced **25 `Error: "Unexpected
token: is_capped_by_modifier"`** parse failures. This token is the sibling of B-3 and is now
invalid. It is used across **8+ repo files**:

- `buildings/btr_planetarystations_buildings.txt`, `buildings/btr_planet_unique_buildings.txt`
- `districts/btr_planetarystations_districts.txt`
- `pop_jobs/00_other_jobs.txt`, `03_worker_jobs.txt`, `04_gestalt_jobs.txt`,
  `06_event_jobs.txt`, `13_machine_age_jobs.txt`
- **Fix:** migrate `is_capped_by_modifier` (and B-3's `inherits_capped_modifiers_from`) to the
  4.4 `shared_capacity_modifier` pool model. Do these together.

---

## B-6 — `common/star_classes/00_star_classes.txt` override broken (HIGH — confirmed)

4.4's stellar-classification rework changed the `star_classes` schema. The mod's override
(`common/star_classes/00_star_classes.txt`) is stale and now throws in the baseline log:
`Unexpected token: stars` (×23), `Unexpected token: name` (×23), `Unexpected token:
entropy_crystals` (×14), plus **duplicate-key spam** (`Object with key: random_list already
exists … star_classes` ×22).

- **Fix:** re-merge against vanilla 4.4.x `common/star_classes/` (new base + re-apply BtR star
  content), or — if BtR's additions are purely additive — drop the `00_*` override and move BtR
  stars into a mod-only `btr_star_classes.txt`. Relates to the `planet_classes` re-merge in
  `02-…`.

---

## B-7 — `planet` → `colony` scope errors (HIGH — confirmed, Carrier/Colony rework)

4.4 split planet logic into the new **Carrier/Colony** scope. The baseline log shows **64**
`Wrong scope … Supported Scopes: planet / Current Scope: colony` errors (plus `Wrong scope for
trigger 'has_planet_flag'`). Offending repo files:

| File | hits |
|------|------|
| `zones/btr_planetarystations_zones.txt` | 22 |
| `buildings/btr_planetarystations_buildings.txt` | 10 |
| `megastructures/btr_planetary_station.txt` | 6 |
| `buildings/07_amenity_buildings.txt` | 6 |
| `buildings/05_research_buildings.txt` | 4 |
| `buildings/02_government_buildings.txt` | 3 |
| `buildings/{04_manufacturing,00_capital,btr_empire_tradition}_buildings.txt` | 2 each |
| `events/game_start.txt` | 1 |

The **Planetary Stations** custom feature is the worst hit. **Fix:** audit these triggers/effects
for the colony scope — use the Colony/Carrier scope or `carrier_is_type`, or re-scope via
`planet = { … }` / `owner` as appropriate. This is broader than a token rename and needs
per-site review; see `03-…` §E.

---

## Summary

| ID | Severity | File(s) | Action |
|----|----------|---------|--------|
| B-1 | Mandatory | `descriptor.mod` | Bump to `v4.4.*` |
| B-2 | High ✅log | `pop_categories/03_unemployment.txt`, 9 `pop_jobs/*.txt` | Remove unemployment categories + strip promotion/demotion (111+25 parse errors); migrate to `forced_integration` |
| B-3 | High ✅log | `districts/02_rural_districts.txt:692` | Convert `inherits_capped_modifiers_from` → `shared_capacity_modifier` |
| B-4 | Watch | branch-office buildings, defines | Re-verify renamed tokens after re-merge |
| B-5 | High ✅log | 8+ files (planetary-stations + pop_jobs) | Convert `is_capped_by_modifier` → `shared_capacity_modifier` (25 errors) |
| B-6 | High ✅log | `star_classes/00_star_classes.txt` | Re-merge to 4.4 schema or move to mod-only file (60+ errors) |
| B-7 | High ✅log | planetary-stations + 5 overridden building files | Fix `planet`→`colony` scope (64 errors); Carrier/Colony rework |

✅log = directly confirmed by the Phase 0 baseline `error.log` (see `06-…`).
