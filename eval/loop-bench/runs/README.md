# loop-bench runs

Each folder is one run of agents on loop-bench's tasks (`../README.md`). A run's `README.md` has
its question, its numbers and its result; a folder with a letter suffix (`r14b`, `r22c`) is a
second stream or a later scoring of the run before it, and its README points there. Inside a run,
each agent has a folder per task with its log, its final and its report.

## Runs

| run | what it tested |
|---|---|
| [r1](r1/README.md) | One-shot, best-of-24, plain Claude Code and the first evolve on six tasks: evolve lost to plain 2–4 |
| [r2](r2/README.md) | Plain against evolve v2 on nine tasks, three of them new |
| [r3](r3/README.md) | v3, a short skill with a ceiling check: not adopted |
| [r4](r4/README.md) | v3.1 (search until the budget is spent) on dedup: not adopted |
| [r5](r5/README.md) | A second v2 agent on dedup: was v2's win the method or luck? |
| [r6](r6/README.md) | v2.1 (v2 plus a noise rule and a ceiling check): not adopted |
| [r7](r7/README.md) | v2.2, one dedup agent before the queue moved to `claude -p` |
| [r8](r8/README.md) | v2.3 (a bound-based ceiling check and a limits note): not adopted; found the tsp hang on duplicate points |
| [r9](r9/README.md) | v2.4 (an awkward-input check before reporting), and v2 on Sonnet: neither adopted |
| [r10](r10/README.md) | v2.5 (the awkward-input check narrowed to failures): not adopted |
| [r11](r11/README.md) | v2.6 (two independent searches in subagents): not adopted, four times the cost |
| r12 | Plain, the one-line nudge and v2 on cache under the neutral brief every later run uses (no README; its plain agents, with run 14's, are the cache baseline of runs 13–16) |
| [r13](r13/README.md) | Variant C against v2 on cache: not adopted |
| [r14](r14/README.md) | Variants D and E, more nudge and plain agents, on cache (with `r14b`) |
| [r15](r15/README.md) | Plain, nudge, v2, E and F on dedup and speedup (with run 17): F's stop rule is picked |
| [r16](r16/README.md) | Variant F on cache (with `r16b`, `r16c`) |
| [r17](r17/README.md) | More F, v2, E and plain on the timed tasks; scored with run 15 |
| [r18](r18/README.md) | G and H, F after a fresh review, on cache and the timed tasks (with `r18b`–`r20`) |
| [r21](r21/README.md) | Arms only: I and J written; J is measured in run 22 |
| [r22](r22/README.md) | Variant J on dedup, speedup and cache (with `r22b`–`r22d`) |
| [r23](r23/README.md) | Variant L, J with a 15-minute default (with `r23b`–`r23d`) |
| [r24](r24/README.md) | Variant M, L plus "use the minutes" and modes chosen by the user's words (with `r24b`–`r24e`) |
| [r25](r25/README.md) | Variant N, M plus the paragraph on other skills' files, and more M on cache (with `r25b`, `r25c`, `r26`, `r26b`) |
| [r27](r27/README.md) | N2, the text evolve ships (with `r27b`, `r27c`) |
| [r28](r28/README.md) | evolve's claim scored once on a secret test seed: plain, N2, Q, R and S on dedup and cache |
| [r29](r29/README.md) | S against N2 with a same-budget nudge control, chosen by a rule written before the run, reported on a fresh secret test seed: N2 stays |
| [r30](r30/README.md) | evolve on Sonnet (with r30s, S on Sonnet) and on Fable (r30f), cache only |
| [stress](stress/README.md) | Every final so far on legal but awkward inputs |

`process_metrics.json` is `../process_metrics.py`'s output over all runs.

## Arms

| arm | what it is |
|---|---|
| plain (`iter` in runs 1–11) | Claude Code with the task and no skill |
| oneshot, bon | Run 1 only: the first of 24 candidates written without running anything, and the best of them |
| nudge | Plain plus one line: "Do not stop at the first answer that works; keep improving it while the scorer budget lasts." |
| v2 … v2.6, v3, v3.1 | Early evolve texts (runs 1–11); v2 was the shipped text until run 27 |
| C | v2, stopping only after half the budget and two rounds without a gain |
| D | A lean 20-line evolve: stop only when the budget is spent |
| E | v2 with step 5 replaced by "stop only when the official scorer calls are spent" |
| F | E plus a `calls left` counter in the log |
| G, H | F plus a fresh review's findings; H puts one sentence back to F's wording |
| I | H plus a rule for candidates that tie within noise; written, not run |
| J | F's step 5 word for word, the review's points moved into a Budget paragraph |
| K | J plus I's tie rule; written, not run |
| L | J with a 15-minute default limit |
| M | L plus "use the minutes" and modes chosen by the user's words; `mx` agents add "take your time" |
| N | M plus a paragraph on reading other skills' files |
| N2 | N after a final review: the text in `plugins/anti-skill/skills/evolve/SKILL.md` |
| Q, R, S | Run 28: N2 with a written backlog of approaches (Q), Q with a fixed end reserve (R), the scorer as the search signal when calls are cheap (S) |
