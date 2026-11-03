# Run 7: v2.2, one agent before the queue moved to `claude -p`

`candidate/SKILL.md` is v2.2: v2.1 plus "find what the scorer rejects first", timing like the
scorer, "attack the harness", a stop rule of "only at the budget or the ceiling", a bound-based
ceiling check and a limits note, revised after a fresh review. Only dedup ran: the overnight loop
stalled, and the next morning's data changed the plan.

dedup held-out (run 2's seed, five interleaved scorings, `dedup_repeats_a.json`): v2.2 86.75
against v2.1 88.28, v2 92.84 and 95.46, plain 77.77. 6 of 24 calls, two of them lost to imports
the task does not allow, despite the new rule. Both variants carrying the noise rule (v2.1, v2.2)
sat 6–8% under both v2 runs, which led to v2.3 (run 8) without it.
