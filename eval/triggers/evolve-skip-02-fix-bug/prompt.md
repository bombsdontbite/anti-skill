---
tags: [evolve, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

pack() below puts an item bigger than the capacity into its own bin instead of raising. Fix it so it raises ValueError.

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
