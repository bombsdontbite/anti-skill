# Runs 15 and 17: plain, nudge, v2, E and F on the timed tasks (dedup, speedup)

Same neutral brief as run 12 for every arm; one agent at a time, nothing else running. Run 15
has two agents per arm; run 17 adds F 3–4, v2 c, E 3 and plain 3 (`../r17`). All finals of
both runs were then scored together on the held-out seed `anti-skill-heldout-r2`, five times
each, interleaved, on an idle machine (`../r17/dedup_heldout.json`, `../r17/speedup_heldout.json`).
Percentages are against the mean of the three plain agents under this brief.

| arm | dedup, vs plain | speedup, vs plain | dedup cost | speedup cost |
|---|---|---|---|---|
| plain (3) | 0% (−7…+8%) | 0% (−21…+42%) | $0.30 | $0.23 |
| nudge (2) | +6% (+2, +10) | +18% (+51, −15) | $0.98 | $1.04 |
| v2 (3) | +17% (+10, +21, +20) | +37% (+55, +25, +31) | $1.54 | $0.81 |
| E (3) | +25% (+7, +14, +53) | +50% (+43, +52, +54) | $2.27 | $0.75 |
| **F (4)** | **+40%** (+39, +34, +39, +50) | +44% (+56, +42, +56, +20) | $3.24 | $0.96 |

Costs are the mean per agent. Every agent stopped early on these tasks (2–19 of 24 calls); a
scorer call takes tens of seconds here.

**Result:** on dedup every F agent (worst +34%) beat every v2 agent (best +21%). On speedup the
evolve arms are close and plain itself spreads from −21% to +42%, so the order there is not
settled. With cache (F +5.4%, v2 +2.8%), F is the pick: `evolve` takes F's stop rule.

Under the old brief (runs 2–11) plain scored higher on both tasks (dedup 79.3, speedup 53.3
against 70.9 and 38.3 here): the neutral brief makes plain stop sooner, so these percentages
are not comparable with the README's earlier ones.
