# Choosing items under several limits

We pick items to fund. Each has a value and uses two or three resources (budget, staff hours,
floor space); the total use of each resource must stay within its capacity, and an item is
taken whole or not at all. The current code, `candidate_baseline.py`, sorts items by value per
unit of resource and takes whatever still fits; I want more value from the same limits.

Write a Python file defining:

    def solve(values: list[int], weights: list[tuple[int, ...]], capacities: list[int]) -> list[int]

`weights[i][k]` is how much of resource `k` item `i` uses and `capacities[k]` is the limit for
resource `k`, all positive integers. Return the indices of the items you take.

Better means more value: the score is the average, over a set of instances, of your total
value divided by the current code's on the same instance (so the baseline scores 1.0).
Instances have a few hundred items; in some, value has nothing to do with resource use, in
others it follows it closely.

Constraints: at most 1 second of wall-clock time per instance; one slow instance makes the
whole run invalid, as does an index out of range, an item taken twice or a resource over its
capacity. Do not hard-code instances; the final score is taken on instances you have not seen.
Pure Python 3 standard library only (math, heapq, bisect, collections, itertools, random,
time, …); no file access, eval/exec, getattr or dunder attributes — the scorer rejects the
file outright.

Score a candidate with `python3 score.py my_candidate.py --split train`.
