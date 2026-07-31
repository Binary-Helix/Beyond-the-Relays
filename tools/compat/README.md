# tools/compat — Stellaris 4.4 migration tooling

Re-runnable scripts supporting the 4.0.23 → 4.4.x compatibility effort
(see `COMPAT-AUDIT-4.4-PEGASUS-2026-06-17/08-updated-plan-2026-07-31.md`).
Python 3.10+, stdlib only. The game ignores this directory.

| Script | Purpose |
|--------|---------|
| `collisions.py` | Inventory of mod files that hard-override vanilla (same relative path), with whitespace-normalized divergence and deletion candidates (identical overrides). Re-run after every vanilla patch. |
| `errorlog_report.py` | Normalizes `error.log` into a (subsystem, signature, count) table. `--diff base.log new.log` prints **net-new signatures** — the exit gate for every migration phase (exit code 1 if any). |
| `token_scan.py` | Burndown of deprecated 4.0-era tokens (promotion/demotion, `is_capped_by_modifier`, unemployment keys, …). Phase 1 done = all zero. Ignores comments. |
| `snapshot_base.py` | Copies old-vanilla (4.0.23) counterparts of every colliding file into `base-4.0/` as 3-way merge bases. |

## Getting the 4.0.23 base (one-time, manual)

Steam keeps old Stellaris versions on the Betas tab:
Steam → Stellaris → Properties → Betas → select the `4.0.x` branch,
let it download, **copy the install** to e.g. `E:\tmp\stellaris-4.0.23`,
then switch the beta back to `None` to restore 4.4.x. Then run:

```
python tools/compat/snapshot_base.py --vanilla E:\tmp\stellaris-4.0.23
```

`base-4.0/` is gitignored (vanilla content is Paradox's, and it's large);
each contributor snapshots locally.

## Typical phase workflow

1. Make changes.
2. Launch the game (junction `Documents/…/mod/btr_skunkworks` → this repo),
   let it load or crash.
3. `python tools/compat/errorlog_report.py --diff <phase-baseline>.log
   "%USERPROFILE%/Documents/Paradox Interactive/Stellaris/logs/error.log"`
4. Gate: net-new = 0. Also `token_scan.py` counts at/below phase target.
