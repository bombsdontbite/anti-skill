# Run 22: variant J on all three tasks

`../r21/arm-j/SKILL.md` (J): F's text with step 5 word for word, and the review's must-fix points
(no budget given, calls kept for the end, a ceiling) in one **Budget** paragraph in section 1.
Dedup in `../r22c`, speedup in `../r22d` (one agent at a time), cache in this folder and
`../r22b` (two at once). Held-out seed `anti-skill-heldout-r2`; dedup and speedup scored together
with every earlier final (`../r22c/dedup_heldout.json`, `../r22d/speedup_heldout.json`).
% against the plain agents under the same brief.

| task | J | F | v2 | J minutes | J cost |
|---|---|---|---|---|---|
| dedup | +36% (+39, +24, +36, +44) | +41% (4) | +18% (3) | 30.0, 11.6, 13.4, 33.3 | $1.79–5.07 |
| speedup | +54% (+56, +52) | +44% (4) | +37% (3) | 5.1, 4.1 | $0.82–0.94 |
| cache | +5.7% (+5.6, +5.3, +5.8, +6.0) | +5.4% (6) | +2.8% (5) | 33.0, 15.0, 26.7, 20.8 | $2.49–3.74 |

Cache minutes overlap the other stream.

**Result:** J keeps F's quality (level on dedup, ahead on speedup and cache) with the review's
fixes, so moving them out of step 5 was what mattered (H, with them inside step 5, scored +23% on
dedup). It is the slowest variant: over 20 minutes on dedup and cache. Run 23 (L) is J with a
15-minute default limit, the author's choice of 2026-10-29.
