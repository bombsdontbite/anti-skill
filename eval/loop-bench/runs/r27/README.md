# Run 27: N2, the text evolve ships

`arm-n2/SKILL.md` (N2): N after a final fresh review of the whole text. Every change is outside
step 5:
- the Budget paragraph: "if the user named no time" (a calls budget alone keeps the 15-minute
  default); "quick" means the agent's time, not the code's speed, and keeps the harness and the
  held-out check; "take your time" writes `minutes left: none`; unclear wording uses the default;
  a proposed number of calls must fill the time budget; a reserve of calls and minutes for the end
  that step 5's counters exclude; the only exceptions to step 5's stop rule are a scorer error and
  a score already at its maximum ("a correct candidate is not that", where N read "every test
  passes" as a ceiling);
- the description says the default time and when not to use the skill;
- the opening's absolute claim about FunSearch and AlphaEvolve is softened; Output reports the
  budget and mode announced at the start.

Dedup in `../r27c` (one at a time, scored with every timed final in
`../r27c/dedup_heldout.json`), cache here and in `../r27b` (two at once). % against the plain
agents under the same brief.

| task | N2 | N | M | v2 |
|---|---|---|---|---|
| dedup | +26% (+17, +20, +30, +36), 9.1–12.1 min | +26% | +19% | +18% |
| cache | +4.8% (+5.9, +4.3, +4.1, +4.9) | +3.8% (8) | +4.2% (8) | +2.8% |

**Result:** the review's fixes cost nothing and N2's four cache agents had no miss. N2 replaces
v2 in `plugins/anti-skill/skills/evolve/SKILL.md`.
