# Scheduling jobs on identical machines

We run jobs on m identical machines, one job at a time per machine, never interrupted. Each job
has a release time (it cannot start earlier), a duration, a deadline and a weight (the cost of
each unit of lateness). We use earliest deadline first (`candidate_baseline.py`); I want less.

Write a Python file defining:

    def schedule(jobs: list[tuple[int, int, int, int]], m: int) -> list[tuple[int, int, int]]

`jobs[j] = (release, duration, deadline, weight)`, all integers. Return one `(job, machine,
start)` triple per job, `machine` in `0 .. m-1`, integer `start`; a job ending after its deadline
costs `weight × (start + duration − deadline)`.

Better means cheaper: the score is minus the average, over a set of instances, of your total
weighted lateness divided by earliest-deadline-first's on the same instance (the baseline
scores -1.0). Instances have a couple of hundred jobs and a handful of machines.

Constraints: at most 1 second of wall-clock time per instance; a missing or repeated job, a
start before release, or an overlap on one machine makes the whole run invalid. Do not
hard-code instances; the final score is taken on instances you have not seen. Pure Python 3
standard library only (math, heapq, bisect, collections, itertools, random, time, …); no file
access, eval/exec, getattr or dunder attributes — the scorer rejects the file outright.

Score a candidate with `./score my_candidate.py`.
