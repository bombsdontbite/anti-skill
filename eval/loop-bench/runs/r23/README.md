# Run 23: variant L (J with a 15-minute default limit)

`arm-l/SKILL.md`: J's Budget paragraph says the search runs until the calls are spent or about 15
minutes have passed (the author's choice of 2026-10-29), and step 5 tracks `calls left, minutes
left`. Dedup in `../r23c` (one at a time), cache in this folder and `../r23b` (two at once). The
run was paused when the laptop was needed for other work: cache has 2 of 4 agents. Speedup ran later
(`../r23d`): +23% (−9, +55), scored with every timed final in `../r24e/speedup_heldout.json`.

| task | L | J | v2 | L minutes |
|---|---|---|---|---|
| dedup | +23% (+35, +4, +22, +32) | +35% | +17% | 9.7, 4.4, 10.3, 11.3 |
| cache | +5.7% (+5.6, +5.8) | +5.7% | +2.8% | about 9 |

**Result:** the limit holds and costs nothing on cache, but on dedup L keeps two thirds of J's
gain, about what v2 gets in the same time plus six points. Agents stopped at 4–11 minutes, reading
"about 15 minutes" as leave to finish early. Run 24 (M) adds "use them, do not stop sooner" and
the modes the author chose: quick about 5 minutes, default about 15, "take your time" without a
time limit.
