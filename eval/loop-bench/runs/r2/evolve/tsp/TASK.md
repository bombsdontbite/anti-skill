# Short tours for 2D points

I have sets of 200 points in the unit square and need a closed tour that visits every point
exactly once and returns to the start, as short as possible (straight-line distances). The
current code, `candidate_baseline.py`, uses nearest neighbour; I want something better.

Write a Python file defining:

    def solve(points: list[tuple[float, float]]) -> list[int]

Return the visiting order as a permutation of the indices `0 .. len(points)-1`. The tour closes
back to its first index automatically.

Better means shorter: the score is minus the average, over a set of instances, of your tour
length divided by the nearest-neighbour tour length on the same instance (so the baseline
scores -1.0). Some instances are spread evenly, some are clumpy.

Constraints: at most 1 second of wall-clock time per instance; one slow instance makes the
whole run invalid, as does a list that is not a permutation. Do not hard-code instances; the
final score is taken on instances you have not seen. Pure Python 3 standard library only
(math, heapq, bisect, collections, itertools, random, time, …); no file access, eval/exec,
getattr or dunder attributes — the scorer rejects the file outright.

Score a candidate with `./score my_candidate.py`.
