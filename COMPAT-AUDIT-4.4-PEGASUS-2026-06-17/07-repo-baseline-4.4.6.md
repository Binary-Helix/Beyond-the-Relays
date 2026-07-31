# error.log report — `COMPAT-AUDIT-4.4-PEGASUS-2026-06-17\07-repo-baseline-4.4.6-error.log`

**1002 parsed error lines**

## By subsystem

| count | subsystem |
|---|---|
| 242 | persistent.cpp |
| 149 | economic_unit_template.cpp |
| 102 | parser_deferred_database_objects.cpp |
| 69 | spritetype.cpp |
| 63 | trigger.cpp |
| 58 | assetfactory_audio.cpp |
| 42 | ai_economic_strategy.cpp |
| 39 | portraits.cpp |
| 37 | job_type.cpp |
| 32 | pdx_particle.cpp |
| 18 | ambient_object_database.cpp |
| 16 | ship_size.cpp |
| 15 | pdx_audio.cpp |
| 13 | texturehandler.cpp |
| 13 | namelist.cpp |
| 12 | modifier.cpp |
| 11 | onaction.cpp |
| 9 | buttontype.cpp |
| 9 | 3dicontype.cpp |
| 8 | effect.cpp |
| 8 | inline_script_database.cpp |
| 8 | event.cpp |
| 7 | ship_growth_stage.cpp |
| 4 | pdxassetutil.cpp |
| 4 | ai_budget_entry.cpp |
| 3 | trait.cpp |
| 2 | strategic_resource.cpp |
| 1 | dlc.cpp |
| 1 | pdx_audio_util.cpp |
| 1 | pdx_audio_sdl.cpp |

## Top signatures (top 30)

| count | subsystem | signature |
|---|---|---|
| 111 | persistent.cpp | Error: "Unexpected token: promotion, line N |
| 33 | economic_unit_template.cpp | Failed to read key reference starbase_waystations_modules from database  file: common/starbase_modules/00_waystation_modules.txt line N |
| 26 | economic_unit_template.cpp | Failed to read key reference starbase_arkship_upgrades from database  file: common/starbase_buildings/00_arkship_colony_buildings.txt line N |
| 25 | persistent.cpp | Error: "Unexpected token: is_capped_by_modifier, line N |
| 25 | persistent.cpp | Error: "Unexpected token: demotion, line N |
| 25 | economic_unit_template.cpp | Failed to read key reference starbase_arkship_upgrades from database  file: common/starbase_modules/00_arkship_weapon_modules.txt line N |
| 23 | persistent.cpp | Error: "Unexpected token: name, line N |
| 23 | persistent.cpp | Error: "Unexpected token: stars, line N |
| 22 | trigger.cpp | Wrong scope for trigger 'has_planet_flag' at  file: common/zones/btr_planetarystations_zones.txt line N |
| 20 | economic_unit_template.cpp | Failed to read key reference starbase_arkship_upgrades from database  file: common/starbase_buildings/00_arkship_component_buildings.txt line N |
| 16 | parser_deferred_database_objects.cpp | Failed to deferred read key reference ap_defender_of_the_galaxy_nomads from database  file: common/resolutions/01_resolutions_nemesis.txt line N |
| 14 | persistent.cpp | Error: "Unexpected token: entropy_crystals, line N |
| 10 | trigger.cpp | Wrong scope for trigger 'has_planet_flag' at  file: common/buildings/btr_planetarystations_buildings.txt line N |
| 9 | economic_unit_template.cpp | Failed to read key reference starbase_arkships from database  file: common/ship_sizes/29_nomads_dlc_ships.txt line N |
| 7 | economic_unit_template.cpp | Failed to read key reference starbase_arkship_upgrades from database  file: common/starbase_modules/00_arkship_utility_modules.txt line N |
| 7 | parser_deferred_database_objects.cpp | Failed to deferred read key reference ap_defender_of_the_galaxy_nomads from database  file: events/ambition_events.txt line N |
| 6 | trigger.cpp | Wrong scope for trigger 'has_planet_flag' at  file: common/buildings/07_amenity_buildings.txt line N |
| 6 | persistent.cpp | Error: "Unexpected token: custom_demotion_loc, line N |
| 6 | persistent.cpp | Error: "Unexpected token: custom_demotion_icon, line N |
| 6 | trigger.cpp | Wrong scope for trigger 'has_planet_flag' at  file: common/megastructures/btr_planetary_station.txt line N |
| 6 | economic_unit_template.cpp | Failed to read key reference starbase_arkship_upgrades from database  file: common/starbase_modules/00_arkship_spinal_modules.txt line N |
| 6 | parser_deferred_database_objects.cpp | Failed to deferred read key reference cruise_passenger_unemployment from database  file: common/buildings/24_nomads_buildings.txt line N |
| 5 | economic_unit_template.cpp | Failed to read key reference starbase_waystations_modules from database  file: common/starbase_modules/00_waystation_modules.txt:N(inline_script) common/inline_ |
| 4 | trigger.cpp | Wrong scope for trigger 'has_planet_flag' at  file: common/buildings/05_research_buildings.txt line N |
| 4 | economic_unit_template.cpp | Failed to read key reference pop_category_slave from database  file: common/pop_categories/02_other_categories.txt line N |
| 4 | event.cpp | show_sound for event btr_council_resolutions.N is referencing inexistent sound btr_event_granted_council_spectre |
| 4 | effect.cpp | Error: "Unexpected token: integrity, line N |
| 4 | inline_script_database.cpp | Unknown inline_script "ship_components/collateral_damage" in file: " file: common/component_templates/00_weapons_extra_large.txt line N |
| 4 | parser_deferred_database_objects.cpp | Failed to deferred read key reference tiny from database  file: events/machine_age_crisis_events.txt line N |
| 4 | parser_deferred_database_objects.cpp | Failed to deferred read key reference small from database  file: events/machine_age_crisis_events.txt line N |

## Most-implicated files (top 30)

| count | file |
|---|---|
| 41 | `common/starbase_modules/00_waystation_modules.txt` |
| 35 | `gfx/portraits/portraits/btr_asari_01_portraits.txt` |
| 26 | `common/starbase_buildings/00_arkship_colony_buildings.txt` |
| 25 | `common/starbase_modules/00_arkship_weapon_modules.txt` |
| 22 | `common/zones/btr_planetarystations_zones.txt` |
| 20 | `common/starbase_buildings/00_arkship_component_buildings.txt` |
| 19 | `events/machine_age_crisis_events.txt` |
| 16 | `common/resolutions/01_resolutions_nemesis.txt` |
| 11 | `common/economic_plans/06_beyond_endgame.txt` |
| 10 | `common/ambient_objects/realspace_system_effects.txt` |
| 10 | `common/buildings/btr_planetarystations_buildings.txt` |
| 10 | `common/economic_plans/05_endgame.txt` |
| 10 | `events/grand_archive_events.txt` |
| 9 | `common/ship_sizes/29_nomads_dlc_ships.txt` |
| 9 | `common/economic_plans/03_advanced.txt` |
| 8 | `common/ambient_objects/realspace_ambient_objects.txt` |
| 7 | `common/starbase_modules/00_arkship_utility_modules.txt` |
| 7 | `events/ambition_events.txt` |
| 6 | `common/buildings/07_amenity_buildings.txt` |
| 6 | `common/global_ship_designs/event_ship_designs_anomalies.txt` |
| 6 | `common/megastructures/btr_planetary_station.txt` |
| 6 | `common/starbase_modules/00_arkship_spinal_modules.txt` |
| 6 | `common/buildings/24_nomads_buildings.txt` |
| 6 | `common/solar_system_initializers/overlord_initializers.txt` |
| 5 | `events/galactic_features_events.txt` |
| 5 | `events/nemesis_crisis_events.txt` |
| 4 | `interface/WIP_loadgame_view.gui` |
| 4 | `common/buildings/05_research_buildings.txt` |
| 4 | `common/pop_categories/02_other_categories.txt` |
| 4 | `common/economic_plans/03_advanced.txt:165(inline_script)` |

---

## Run context & June "re-verify" resolutions

- **Run:** 2026-07-31, Game **Pegasus v4.4.6**, only `mod/btr_skunkworks.mod` enabled
  (junction → `E:\Repositories\btr_skunkworks`, repo confirmed via BtR static modifiers in logs).
- **Outcome:** crash during load (dump `crashes/stellaris_20260731_013505`) — expected per
  `06-…`; error.log written before the crash. Raw log archived as
  `07-repo-baseline-4.4.6-error.log` (this is the diff baseline for all phase gates).
- **Cleaner than the devbuild run:** 1,002 parsed error lines vs 2,641 (Jul 5 Workshop devbuild).
- **June 🔁 items resolved:**
  - `btr_anomalies.txt` 133-error syntax cluster: **deployed-copy artifact — NOT in repo**
    (repo shows only 1 duplicate-event-id warning, `btr_anomaly.13` at line 421).
  - Nomads `starbase_*` cascade: **repo-confirmed** (`starbase_waystations_modules` ×33 etc.)
    — the repo's `ship_sizes`/starbase-era overrides shadow Nomads keys; fixed by Phase 2.6.
