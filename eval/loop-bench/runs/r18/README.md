# Runs 18–20: the reviewed text on cache and the timed tasks

After a fresh review of F, two texts were measured. Same brief as run 12, held-out seed
`anti-skill-heldout-r2`, % against the plain agents under the same brief.

- `arm-g/SKILL.md` (G): F plus all eight review findings, including "Spend a call only on a
  candidate the harness rates near the best". Cache, 4 agents (`r18`, `r18b`).
- `arm-h/SKILL.md` (H): G with that sentence back to F's wording. Timed tasks in `../r18c`
  (folders `g5`, `g6` ran **arm H**: the queue was switched before they started), more dedup
  in `../r20`, cache in `../r19`, `../r19b`.

| text | cache | dedup | speedup |
|---|---|---|---|
| F (runs 15–17) | +5.4% (6) | +41% (4: +40, +34, +40, +50) | +44% (4) |
| G | +4.8% (4), 38% of the budget | – | – |
| H | +5.2% (4) | +23% (4: +23, +38, +11, +22) | +35% (2) |
| v2 | +2.8% (5) | +18% (3) | +37% (3) |

Dedup and speedup were scored together with runs 15 and 17 (`../r20/dedup_heldout.json`,
`../r18c/speedup_heldout.json`).

**Result:** G's extra sentence gave agents a reason to stop (one said so); H fixed cache but lost
to F on dedup, where three of four H agents scored below every F agent. The review's must-fix
points are kept, but moved out of step 5 in J (run 22), so step 5 reads exactly as tested.
