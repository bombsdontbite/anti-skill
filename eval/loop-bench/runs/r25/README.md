# Runs 25 and 26: N (M plus the stack paragraph) solo, and more M on cache

`arm-n/SKILL.md` (N): M with one paragraph in section 1, "Other skills' files" (use a trusted
`scorer/` from make-scorer and `profile/result.json` from profile-first if they are there; reviewed
once and fixed before measuring). On loop-bench neither file exists, so this measures whether the
paragraph costs anything solo. Dedup in `../r25c` (one at a time, scored with every timed final in
`../r25c/dedup_heldout.json`); cache in this folder, `../r25b`, and `../r26`, `../r26b` (four more
N and four more M, interleaved, after N's first four looked low). % against the plain agents under
the same brief.

| task | N | M | v2 |
|---|---|---|---|
| dedup | +26% (+25, +30, +18, +29), 8.5–12.3 min | +20% (4) | +18% (3) |
| cache | +3.8% over 8 (+4.1, +0.6, +4.2, +0.2, +6.0, +4.7, +5.0, +5.6) | +4.2% over 8 (+5.3, +5.7, +1.3, +5.5, +0.5, +6.2, +4.0, +4.9) | +2.8% (5) |

No N agent mentioned `scorer/` or `profile/` in its report; times and stop reasons match M's.

**Result:** the paragraph costs nothing solo: N and M are level within their spread on cache (both
have two agents of eight near zero) and N is not worse on dedup. N is the text evolve ships.
