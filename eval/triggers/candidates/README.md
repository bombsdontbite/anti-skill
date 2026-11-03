# Trigger candidates

Three ways to make evolve load on its own on Sonnet, drafted and not yet measured. On Sonnet 5.5
evolve loaded on 3 of its 42 request runs, profile-first took 9 of them and nothing loaded on 30
([trigger results](../RESULTS.md)); a description that led with the user's words did not move it.
Nothing here ships: the plugin under `plugins/anti-skill/` is unchanged until one candidate passes
the rule below.

| Candidate | What changes | Always-on tokens (estimate) |
|---|---|---|
| current | nothing | about 320: the two skills' listing lines |
| [`desc/`](desc/descriptions.json) | both `description:` lines: trigger first, split on "does something already measure it?" | about 310 |
| [`hook-start/`](hook-start/hooks/hooks.json) | a SessionStart hook adds [one routing sentence](hook-start/hooks/session-start.txt) | about 390 (320 + about 60 for the sentence + about 10 for the reminder that carries it) |
| [`hook-prompt/`](hook-prompt/hooks/hooks.json) | a UserPromptSubmit hook adds one line, only when the prompt has a speed or score word | about 320; about 70 more on each prompt that matches |

Token figures are characters divided by four, the same estimate as the 320; `/context` in a
session gives the exact count.

## Wiring

Claude Code loads `hooks/hooks.json` at a plugin's root on its own, so a hook candidate needs no
`plugin.json` field (a `hooks` field there is merged with that file, so naming the same file
would load it twice). `apply.py` copies a candidate into a copy of the plugin and refuses the
shipped one:

```
git worktree add ../anti-skill-arm-desc HEAD
python3 eval/triggers/candidates/apply.py desc ../anti-skill-arm-desc/plugins/anti-skill
```

Run `apply.py` from this checkout: it refuses the `plugins/anti-skill` next to itself, so that
arm worktrees are the only ones changed.

`claude plugin eval` loads the plugin's skills, hooks and agents, and hooks run outside the run's
sandbox, as you; your own settings and hooks are not loaded.

- **hook-start** prints a text file at `startup`, `clear` and `compact`; plain stdout of a
  SessionStart hook is added as context. `|| true` keeps it silent and at exit 0 if the file is
  missing.
- **hook-prompt** is POSIX `sh`, `sed`, `tr` and `grep`: no network, no files written, no Python.
  It reads only a JSON object with a string `prompt`, drops the `cwd` and `transcript_path` values
  (a folder named `bench` would otherwise match every prompt), and matches whole words. Its exit
  status is always 0, and it prints nothing on bad input or when a tool is missing.
  `test_candidates.py` holds it to a median under 50 ms and a 900 KB paste under a second.

### Where hook-prompt fires when it should not

It fires on the word, not the intent. Any prompt with "slow", "score", "profile", "optimise" or
"benchmark" gets the line: "what does this profiler output mean", "explain the scoring function",
"write a benchmark for this", "is the slow query log on?". The line itself says to ignore it
unless the request is to change code to run faster or score higher, so the risk is a nudge, not a
load, and the near misses measure it. "speed" as a noun matches too.

Its words are English only, so it never fires on a request in another language. Every request in
the suite is in English since 2026-11-03.

## Measurement plan (pre-registered; not run)

- **Model:** Sonnet 5.5 first. Fable and Opus only for the winner, as a no-regression check.
- **Arms:** current, desc, hook-start, hook-prompt, each in its own worktree. Order: evolve's half
  current → desc → hook-start → hook-prompt, then profile-first's half in the reverse order.
- **Cases:** the existing 54 (`evolve-*` and `profile-*`), 3 runs each: 42 should-load runs and
  39 near-miss runs per skill.
- **Smoke first:** one should-load case of each hook arm, `--runs 1 --keep-temp`; the hook's text
  must be seen in that run's kept files (transcript or debug log), or the arm is not run.

From each arm's worktree:

```
claude plugin eval . --eval-dir eval/triggers --case 'evolve-*' --model sonnet --ablation none --scaffold --no-publish --max-cost-usd 20
claude plugin eval . --eval-dir eval/triggers --case 'profile-*' --model sonnet --ablation none --scaffold --no-publish --max-cost-usd 20
```

### Decision rule

Counts are runs, from the same session as the current arm. A candidate ships only if all four hold:

1. evolve loads on its own requests at least 9 more times of 42 than current (about +21 points),
   in at least 4 different cases;
2. on the 26 near misses (78 runs), any anti-skill skill loads at most 2 more times than current;
3. profile-first loads on its own requests at most 2 fewer times of 42 than current;
4. evolve's requests go to profile-first no more often than current.

Why 9 and 4 cases: the 3 evolve loads were one case 3 of 3, so runs of a case move together and
the real sample is nearer 14 cases than 42 runs; re-runs so far moved by 0 to 2 runs; and below a
third of requests the README would still have to say that evolve mostly does not load. Why 2:
every model's near misses were 0 or 1 of 39, so 2 more of 78 allows one stray load per skill but
not a hook that nudges a whole case (3 runs) into loading.

If more than one passes, the largest evolve gain wins; within 3 runs, the one with fewer always-on
tokens. If desc and a hook both pass, one more arm, desc with that hook, is held to the same rule.

### Confirmation

The winner and current run once more on the held-out requests written by someone who has not seen
any description, Sonnet 5.5, 3 runs. Confirmed if evolve's gain there is at least +15 points and
at least half its gain above, with near-miss loads within the same +2 per 78 runs. Then the winner
runs once on Fable 5.1: each skill must still load on at least 90% of its requests, with at most
one near-miss load. If it is not confirmed, nothing ships and the result is written up as a loss.

### Cost and time

From the kept runs, a Sonnet near-miss run costs about $0.09 (profile-first's 39 for $3.30), and a
Fable run about $0.22 to $0.27. A should-load run that loads a skill reads its body and costs more;
assume $0.09 to $0.30. Per skill half (81 runs) that is about $7 to $16, so the cap is $20 a half
rather than $15: a run cut by its cap drops the cases that come last, and the comparison with it.

| Step | Runs | Estimate |
|---|---|---|
| Smoke, two hook arms | 2 | under $1 |
| Four arms, Sonnet | 648 | about $55 to $130; at most $160 by the caps |
| Combination arm, if needed | 162 | about $15 to $32 |
| Held-out confirmation, two arms | depends on the set | about $0.20 a run |
| Fable check of the winner | 162 | about $40 |

Wall time: a run takes up to 3 turns and is cut at 180 s; at 30 to 60 s a run, one arm is 1.4 to
2.7 hours at `-j 1`, so the four arms are 5.5 to 11 hours in a row, or about 3 to 5.5 hours at `-j 2`.
The hooks themselves cost nothing measurable next to that.

## Checks

`python3 eval/triggers/candidates/test_candidates.py` checks, without a model: both descriptions
are shorter than the shipped ones and name the other skill; the prompt hook fires on speed and
score words, stays silent otherwise and on bad input, ignores the path fields,
and keeps to its time bounds; the hooks files parse; `apply.py` changes only the description lines
and refuses the shipped plugin.
