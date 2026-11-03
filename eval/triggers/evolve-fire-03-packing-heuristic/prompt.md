---
tags: [evolve, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Find a better heuristic for this bin packing problem. Fewer bins across the benchmark instances is better; `python check.py` packs every instance in data/, verifies capacities and prints the total bin count.

```python
def pack(items, cap):
    bins = []
    for it in sorted(items, reverse=True):
        for b in bins:
            if sum(b) + it <= cap:
                b.append(it)
                break
        else:
            bins.append([it])
    return bins
```
