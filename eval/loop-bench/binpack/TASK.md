# Online bin packing heuristic

Items arrive one at a time and each must be placed into a bin immediately, without knowing
the items still to come. Bins have a fixed capacity; item sizes are positive integers. I want a
better rule for choosing the bin than the one in `candidate_baseline.py`.

Write a Python file defining:

    def priority(item: int, bins: list[int]) -> list[float]

`bins` holds the remaining capacity of every open bin that can still fit the item, followed by
one last entry for a fresh empty bin (that entry equals the full bin capacity). Return one
priority per entry; the item goes into the entry with the highest priority (first one on ties).

Better means fewer bins: the score is minus the average of (bins used / ⌈total size ÷ capacity⌉)
over a set of instances, so -1.0 would be perfect. Instances have a couple of thousand items each
and draw sizes from a few different distributions.

Constraints: the whole run (all instances) must finish within 8 seconds. Do not hard-code
instances or answers; the final score is taken on instances you have not seen. Pure Python 3
standard library only (math, heapq, bisect, collections, itertools, random, …); no file
access, eval/exec, getattr or dunder attributes — the scorer rejects the file outright.

Score a candidate with `python3 score.py my_candidate.py --split train`.
