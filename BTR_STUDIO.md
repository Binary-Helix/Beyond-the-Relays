# BTR Studio

**Beyond the Relays Modding Studio** — the tooling for developing this mod (parser, validator, Language Packs, index, CLI, desktop app) — is developed in a **separate sibling repository**, not here:

```
../btr_studio     (sibling of this mod repository)
```

## What lives where

- **This repository (`btr_skunkworks`)** remains the Stellaris **mod content source**: `common/`, `events/`, `localisation/`, `gfx/`, map data, descriptors — the deployable artifact copied into the Stellaris mods directory.
- **`btr_studio`** owns all application code, architecture, research, decisions, and the engineering workflow. Its `AI/` directory is the **authoritative** planning and architecture control plane (migrated out of this repo on 2026-07-14).
- This mod may later contain a `.btr/` directory for project metadata (feature manifests) — provisional, pending the launcher-tolerance check (R-10).

## For contributors

- Mod content changes happen here as normal.
- Studio architecture/workflow questions: see `btr_studio/AI/` (start at `CURRENT_STATE.md` and `ENGINEERING_WORKFLOW.md`).
- The Studio treats this repository as **external input**. It reads mod files and (once safe-writes ship) proposes edits through a reviewed pipeline; it never performs git operations here on its own.

*This is an integration pointer only — the authoritative documents are not duplicated here.*
