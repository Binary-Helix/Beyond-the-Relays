# 03 — New Systems Parity Gaps

Systems and content added across 4.1–4.4 that BtR has **no or partial** coverage for. For full
parity these must be themed to ME canon or deliberately gated. Vanilla paths are under
`F:\SteamLibrary\steamapps\common\Stellaris\common\`.

> Reminder (`00-…`): the mod **not overriding** a long-standing vanilla dir is fine — vanilla
> loads it. Listed below are only genuinely-new systems or new content files relevant to parity.

## A. Nomads (4.4 / Nomads DLC) — INTEGRATE into ME canon (see `04-…`)

| Vanilla path | Mod | Note |
|--------------|-----|------|
| `districts/07_ark_districts.txt` | none | 5 arkship districts (`district_ark_city/_generator/_military/_forever_cruise/_basic`) |
| `pop_jobs/17_nomads_jobs.txt` | none | nomad jobs (cruise crew/passenger, scavenger, herder, whisperer…) |
| `buildings/24_nomads_buildings.txt` | none | Forever Cruise / arkship buildings |
| `zones/05_arkship_zones.txt`, `zone_slots/…` | none | arkship zones + slots |
| `situations/14_nomads_situations.txt` | none | nomad origins/contracts situations |
| `megastructures/29_nomad_arkships.txt`, `30_nomad_waystation.txt`, `31_dyson_gun.txt` | none | arkship/waystation megastructures |
| `starbase_modules/00_arkship_*_modules.txt` (spinal/utility/weapon), `00_waystation_modules.txt` | none | arkship/waystation modules |
| `decisions/15_nomads_dlc_decisions.txt` | none | nomad decisions |
| `inline_scripts/arkship/`, `inline_scripts/contracts/` | none | arkship AI/design + contract scripts |
| `common/missions/` (top-level) | none | **contract/mission system** (`owned_mission`, `issued_mission`, `has_contract*`) |
| New scopes **Carrier / Colony**, trigger `carrier_is_type`, `create_country { is_nomadic = yes }`, `is_nomadic` government/country trigger, `pop_group_can_join_factions` game rule | n/a | Affects planet-scoped events → see `04-…` |

Also: vanilla `districts/02_rural_districts.txt` `convert_to` now lists `district_ark_generator`
(mod's stale copy omits it — `02-…`).

## B. Machine Age (4.3)

| Vanilla path | Mod | Note |
|--------------|-----|------|
| `buildings/20_machine_age_buildings.txt` | none | augmentation bazaars, etc. |
| `pop_jobs/13_machine_age_jobs.txt` | **stale override** | mod has it, frozen at 4.0 (`02-…`) |
| `situations/08_machine_age_situations.txt` | none | machine-age situations |
| `common/mutations/` (top-level) | none | bio-modding/mutations system |
| `megastructure_overclock_types/` (top-level) | none | megastructure overclocking |

## C. Astral Planes (4.2)

| Vanilla path | Mod | Note |
|--------------|-----|------|
| `common/astral_actions/` (top-level) | none | astral rift actions |
| `common/astral_rifts/` (top-level) | none | astral rift terrain system |
| `buildings/18_astral_planes_buildings.txt` | none | astral buildings |
| `pop_jobs/11_astral_planes_jobs.txt` | none | astral jobs |
| `situations/06_astral_planes_situations.txt` | none | astral situations |
| `decisions/09_astral_planes_decisions.txt` | none | astral decisions |

## D. Other DLC / patch content the mod lacks

| System | Representative vanilla files | Mod |
|--------|------------------------------|-----|
| Cosmic Storms | `buildings/19_cosmic_storm_buildings.txt`, `pop_jobs/12_cosmic_storm_jobs.txt`, `situations/07_cosmic_storms_situations.txt`, `storm_types/` | none |
| Grand Archive | `buildings/21_grand_archive_buildings.txt`, `pop_jobs/14_grand_archive_jobs.txt` (**stale override**), `megastructures/20_grand_archive.txt`, `patrons/` | partial/none |
| Biogenesis | `buildings/22_biogenesis_buildings.txt`, `pop_jobs/15_biogenesis_jobs.txt`, `situations/12_biogenesis_situations.txt` | none |
| Shroud | `buildings/23_shroud_buildings.txt`, `pop_jobs/16_shroud_jobs.txt`, `situations/13_shroud_situations.txt`, `megastructures/22_shroud_seal.txt` | none |
| Wilderness / Extreme Frontiers | `districts/05_wilderness_districts.txt`, `buildings/21_wilderness_buildings.txt` / `22_extreme_frontiers_buildings.txt` | none (mod has `14_wilderness_jobs.txt` stub) |
| Swap content | `pop_jobs/99_swap_jobs.txt`, `districts/06_swap_districts.txt` | none |
| Pretriggers | `pop_jobs/000_pretriggers.txt` | none |
| Pop assembly | `buildings/01_pop_assembly_buildings.txt` | none |

> Most of these are not hard breakages (the mod doesn't override them, so vanilla loads them).
> They matter for **parity + ME theming**: an ME total conversion generally wants this content
> either reskinned to ME lore or gated off, not left as raw vanilla. Decide per system in the
> roadmap. The **highest-value targets** are those that intersect player-visible empire setup and
> economy: Nomads (A), Machine Age (B), and new districts/zones.

## E. Engine-level changes affecting existing BtR scripts

- **Carrier/Colony scope split (4.4):** many vanilla planet events were converted to *carrier*
  events for nomad compatibility. BtR's planet-scoped events (700+ event files) should be
  audited for places where `planet` scope assumptions no longer hold and where `carrier_is_type`
  / Colony scope is now expected.
- **Weapon/ship-size fields:** new `collateral_damage/range`, `chain_damage/range/count`,
  `is_orbital_ring`, `construction_capabilities`, `level_tooltip`. Relevant if BtR overrides
  ship sizes / starbase levels (verify `common/ship_sizes`, `starbase_levels` — not in the
  100%-override set, so likely fine, but confirm).
- **Megastructure fields:** new `show_in_build_menu`, tooltip fields; Merged Capital Assembly
  Yards replace Titan/Colossal yards; orbital rings dismantleable.

## F. Verification hooks for this section

When the mod is run on 4.4.1, expect `error.log`/`setup.log` lines referencing missing/duplicate
definitions only for files BtR **overrides** (Section A/B/C "stale override" rows and `02-…`).
Non-overridden new systems won't error — they'll simply appear as un-themed vanilla content
in-game (the parity gap), which is a design issue, not a log error.
