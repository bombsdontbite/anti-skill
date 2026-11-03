# Cache eviction policy

I need a fixed-size cache that gets more hits than LRU (`candidate_baseline.py`) on our access
patterns, which mix hot keys, repeated loops, one-off scans and shifts in what is popular.

Write a Python file defining a class:

    class Cache:
        def __init__(self, capacity: int): ...
        def access(self, key: int) -> bool: ...

`access` is called once per request, in order, and returns True when the key was already cached
(a hit), else False; on a miss you may store the key and evict others. `self.store` must be a set
or dict holding exactly the cached keys, never more than `capacity`, and only the key just
requested may be added. The scorer verifies all of this and counts only real hits.

Better means more hits: the score is the hit rate (hits / requests) averaged over several traces
of tens of thousands of requests each. Capacity is fixed per trace and is in the hundreds.

Constraints: all traces together must finish within 8 seconds. Do not hard-code traces; the
final score is taken on traces you have not seen. Pure Python 3 standard library only (math,
heapq, bisect, collections, itertools, random, …); no file access, eval/exec, getattr or dunder
attributes — the scorer rejects the file outright.

(Candidates are scored later, not by you.)
