---
tags: [evolve, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Explain what this function does and when two records count as duplicates.

```python
def dedup(records):
    out = []
    for r in records:
        if not any(similar(r, o) for o in out):
            out.append(r)
    return out

def similar(a, b):
    return sum(x != y for x, y in zip(a.lower(), b.lower())) <= 2 and abs(len(a) - len(b)) <= 2
```
