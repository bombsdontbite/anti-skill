# Run 24: variant M (L plus "use the minutes" and modes chosen by the user's words)

`arm-m/SKILL.md` (M): L's Budget paragraph rewritten. The default is about 15 minutes ("use them;
do not stop sooner") or until the calls are spent; "a quick answer" means about 5 minutes; "take
your time" means no time limit. The agent says at the start which budget it uses. `max.txt` is the
phrase a "take your time" arm adds to the brief (via `run_queue2.sh`, arm `SKILL.md+max.txt`).
From this run on the runner denies Read on the scorers and audits every queue (`audit.json`).

**Dedup, default mode** (`../r24c`, one agent at a time, scored with every earlier final in
`../r24c/dedup_heldout.json`, % against the plain agents under the same brief):

| text | dedup | minutes | cost |
|---|---|---|---|
| M | +18% (+20, +25, +6, +21) | 10.7, 14.5, 10.8, 11.8 | $1.54–2.47 |
| L | +23% (4) | 4.4–11.3 | $0.88–2.06 |
| J (no time limit) | +35% (4) | 11.6–33.3 | $1.79–5.07 |
| v2 | +16% (3) | about 9 | about $1.5 |

**Set aside:** `m5_loaded` ran while the laptop was in other use (load about 4); cache's 8 s
scoring limit makes such runs invalid, so it is not counted. `m6_killed` was stopped mid-run.

**All results** (dedup and speedup scored together with every timed final on an idle machine,
five times each, interleaved: `../r24e/dedup_heldout.json`, `../r24e/speedup_heldout.json`; cache
re-scored one by one; % against the plain agents under the same brief):

| task | M, default (~15 min) | M, "take your time" | J | v2 |
|---|---|---|---|---|
| dedup | +19% (+21, +28, +7, +21), ~12 min | **+53%** (+42, +65), 33 and 42 min | +36% | +18% |
| speedup | **+54%** (+54, +55) | – | +54% | +38% |
| cache | +4.5% (+5.3, +5.7, +1.3, +5.5) | +5.5% (+4.4, +6.6) | +5.7% | +2.8% |

The "take your time" agents are `../r24e/mx1`, `mx2` (dedup) and `mx3` (`r24`), `mx4` (`r24b`)
(cache); M's speedup agents are in `../r24d`. L's speedup (`../r23d`): +23% (−9, +55).

**Result:** the modes work as meant. The default is at least v2's quality on every task in about
the same time (and +54% against +38% on speedup); "take your time" gives the best dedup of any
arm so far. "Do not stop sooner" made agents use more of the 15 minutes but did not raise
dedup over L's. M is the base for the shipped text; run 25 measures it with the stack paragraph
that reads other skills' files (N).
