# Colouring graphs with fewer colours

Every node of a graph gets a colour so that no edge joins two nodes of the same colour, and I
want as few colours as possible (they are time slots: fewer means a shorter timetable). The
current code, `candidate_baseline.py`, goes through the nodes from the highest degree down and
gives each the smallest colour none of its neighbours has; I want fewer.

Write a Python file defining:

    def color(n: int, edges: list[tuple[int, int]]) -> list[int]

Nodes are `0 .. n-1`; every edge `(u, v)` appears once, in either orientation, and never joins
a node to itself. Return one colour per node, in node order, each an integer in `0 .. n-1`.

Better means fewer colours: the score is minus the average, over a set of instances, of the
number of distinct colours you use divided by the current code's on the same instance (so the
baseline scores -1.0). Graphs have a few hundred nodes; some are random with different
densities, some have structure.

Constraints: at most 1 second of wall-clock time per instance; one slow instance makes the
whole run invalid, as does an edge whose ends share a colour, a missing node or a colour out
of range. Do not hard-code instances; the final score is taken on instances you have not seen.
Pure Python 3 standard library only (math, heapq, bisect, collections, itertools, random,
time, …); no file access, eval/exec, getattr or dunder attributes — the scorer rejects the
file outright.

Score a candidate with `python3 score.py my_candidate.py --split train`.
