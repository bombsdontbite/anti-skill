---
tags: [evolve, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Refactor this to be easier to read. Behaviour must stay exactly the same.

```python
def color(graph):
    """graph: dict node -> set of neighbours. Returns dict node -> colour index."""
    order = sorted(graph, key=lambda n: len(graph[n]), reverse=True)
    colours = {}
    for n in order:
        used = {colours[m] for m in graph[n] if m in colours}
        c = 0
        while c in used:
            c += 1
        colours[n] = c
    return colours
```
