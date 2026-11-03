# Make the duplicate finder fast

`candidate_baseline.py` holds `near_duplicates(records)`, which we run over our catalogue to
find records that are probably the same thing entered twice: it compares the sets of words of
every pair of records and reports the pair when they are at least 80 % alike. It is correct but
far too slow on real volumes. Read its docstring for the exact definition; that definition is
the specification.

Write a Python file defining the same function:

    def near_duplicates(records: list[str]) -> list[tuple[int, int]]

It must report exactly the pairs the reference reports on every input: each pair once, as
`(i, j)` with `i < j`, in any order. Better means faster: the score is the reference's CPU time
divided by yours (the median of a few runs, each in a fresh process, with the time to import
your file counted) on a couple of inputs of a few thousand records each, so the reference
itself scores about 1.0. A missing, extra or repeated pair, on those inputs or on a batch of
small correctness tests with edge cases, makes the run invalid.

Constraints: a run more than about three times slower than the reference is cut off. Do not
hard-code inputs or answers; the final score is taken on inputs you have not seen. Pure Python 3
standard library only (math, heapq, bisect, collections, itertools, …); no file access,
eval/exec, getattr or dunder attributes — the scorer rejects the file outright.

Score a candidate with `python3 score.py my_candidate.py --split train`.
