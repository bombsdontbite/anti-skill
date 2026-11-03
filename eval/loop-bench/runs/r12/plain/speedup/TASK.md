# Make the usage report fast

`candidate_baseline.py` holds `usage_report(sessions, windows)`, which we use for billing: for
every reporting window it adds up rate × overlap length over all sessions and counts how many
sessions overlap the window at all. It is correct but far too slow on real volumes. Read its
docstring for the exact definition; that definition is the specification.

Write a Python file defining the same function:

    def usage_report(sessions: list[tuple[int, int, int]],
                     windows: list[tuple[int, int]]) -> list[tuple[int, int]]

It must return exactly what the reference returns (same order, integers, no rounding) on every
input. Better means faster: the score is the reference's CPU time divided by yours on a few
inputs of a few thousand sessions and a few hundred windows each, so the reference itself
scores about 1.0. Any wrong answer, on those inputs or on a batch of small correctness tests
with edge cases, makes the run invalid.

Constraints: a run more than about three times slower than the reference is cut off. Do not
hard-code inputs or answers; the final score is taken on inputs you have not seen. Pure Python 3
standard library only (math, heapq, bisect, collections, itertools, …); no file access,
eval/exec, getattr or dunder attributes — the scorer rejects the file outright.

Score a candidate with `./score my_candidate.py`.
