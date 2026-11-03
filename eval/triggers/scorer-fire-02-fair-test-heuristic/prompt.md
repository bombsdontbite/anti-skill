---
tags: [make-scorer, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Build me a fair test for this scheduling heuristic, so I can tell whether a new version is really better and not just better on the cases I tried. All we have is the function and two unit tests.

```python
def schedule(jobs, machines):
    """jobs: list of (id, duration). Returns machine index -> list of job ids."""
    load = [0] * machines
    plan = {m: [] for m in range(machines)}
    for jid, d in sorted(jobs, key=lambda j: -j[1]):
        m = load.index(min(load))
        plan[m].append(jid)
        load[m] += d
    return plan
```
