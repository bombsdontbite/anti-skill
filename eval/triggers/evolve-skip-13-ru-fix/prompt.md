---
tags: [evolve, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

pack() ниже падает с TypeError, если в items попадает None. Почини, чтобы None просто пропускался.

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
