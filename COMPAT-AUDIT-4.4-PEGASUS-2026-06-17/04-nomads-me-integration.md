# 04 — Nomads → Mass Effect Canon Integration

**Decision:** integrate the Nomads expansion into ME canon rather than suppress it.

> ⚠️ **Dependency — Codex access required.** The *Mass Effect: Beyond the Relays Codex 2.0*
> Google Doc could not be read programmatically (WebFetch returns only the page chrome, not the
> body; the doc requires authenticated access). The canon mappings below are **proposals** based
> on obvious ME ↔ Nomads parallels and must be confirmed/replaced against the Codex before
> implementation. To unblock: paste the relevant Codex sections, export the doc to text, or grant
> the Google Drive MCP connector access so it can be read directly.

## What Nomads adds (vanilla mechanics to map)

- **Arkships** — massive mobile capital structures that *are* the empire's home; they carry
  pops/buildings via the new **Carrier/Colony** scope and arkship **zones/districts**.
- **Waylines / Waystations** — resource-propagation network and fixed structures.
- **Contracts (missions)** — task-driven, mercenary-style income via the new `common/missions/`
  system (`owned_mission`, `issued_mission`, `has_contract*`, `is_contract_type`).
- **Nomadic origins / `is_nomadic` government & country trigger**, **"Defender of the Galaxy"
  ambition**, nomad jobs, nomad decisions/situations.

## Proposed ME canon mappings (to validate against Codex)

| Nomads mechanic | Candidate ME mapping | Rationale |
|-----------------|----------------------|-----------|
| Arkship empire | **Quarian Migrant Fleet / Flotilla** | The Flotilla *is* a mobile fleet-as-home civilization — the canonical ME nomad. Arkship ≈ liveships / the Rayya. |
| Secondary nomad flavor | **Geth (post-exodus) / drifter remnants, mercenary bands** | Possible alt nomadic origin or gestalt-flavored arkship. |
| Waystations / Waylines | Flotilla supply rendezvous, fuel/resource convoys | Fits the Migrant Fleet's logistics dependence. |
| Contracts / mercenary income | **Mercenary outfits / salvage economy** (e.g. Blue Suns, freelance crews) | Maps cleanly to the task-for-pay loop. |
| "Defender of the Galaxy" ambition | Anti-Reaper / anti-crisis ME framing | Thematically consistent. |

These are starting hypotheses. The Codex likely already specifies how the Migrant Fleet is
represented in BtR (it has an existing **Migrant Fleet** event chain — see below), so integration
should extend that rather than introduce a parallel system.

## Existing BtR hooks to build on (not greenfield)

- BtR already has a **Migrant Fleet** event domain (per the architecture map: Event Chains
  domain) and `naval_contractors`-style civic content. The Nomads integration should connect the
  Quarian Flotilla / Migrant Fleet representation to vanilla arkship mechanics rather than create
  a second nomad system.
- A `# TODO: update for Nomads` marker already exists in
  `common/gamesetup_settings/gamesetup_settings.txt` — confirm and resolve.

## The vanilla-origin / civic leak (must gate either way)

BtR does **not** restrict the empire creator with `playable = { … }` / origin-gating; it relies on
zeroing spawn weights for its own content. Consequence on 4.4.1:

- Vanilla **nomadic origins** (gated `playable = { has_nomads_dlc = yes }`) and nomad civics will
  **appear in the empire creator** for players who own the DLC, breaking the curated ME roster.
- BtR's `interface/select_empire_design.gui` hides the "CUSTOMIZE" button but does **not** filter
  the origin list.

**Required decision per vanilla nomadic origin/civic:** *reskin to ME* (wire into the Migrant
Fleet integration) **or** *hide* (`playable = { always = no }` or an override that gates them out).
Mixed approach likely: reskin the core arkship origin to the Quarian Flotilla; hide the rest.

## Implementation surface (when this phase runs)

1. **Empire setup:** new/aliased ME nomadic origin(s) + government using `is_nomadic`; gate or
   reskin all vanilla nomadic origins/civics.
2. **Arkship content:** themed `districts/07_ark_districts.txt`, `zones/05_arkship_zones.txt`,
   `buildings/24_nomads_buildings.txt`, `pop_jobs/17_nomads_jobs.txt`,
   `megastructures/29_nomad_arkships.txt` + `30_nomad_waystation.txt`, arkship `starbase_modules`.
3. **Contracts:** ME-flavored `common/missions/` content + `situations/14_nomads_situations.txt`.
4. **Events:** audit planet→carrier scope conversions across BtR events (Carrier/Colony,
   `carrier_is_type`); ensure the Migrant Fleet chain interoperates.
5. **on_actions:** register the new nomad/arkship/contract on_actions in BtR's hooks (ties into
   the `00_on_actions.txt` re-merge, `02-…`).
6. **Localisation:** ME names/descriptions for all of the above across 8 languages.

## Open questions for the maintainer (resolve from Codex)

1. Is the Migrant Fleet meant to be a **playable nomadic empire** (arkship origin) or remain an
   NPC/event entity?
2. Which ME faction(s) beyond the Quarians, if any, get nomadic origins?
3. How should Contracts be framed in ME terms (mercenary work, salvage, smuggling)?
4. Keep, reskin, or hide each vanilla nomadic origin/civic?
