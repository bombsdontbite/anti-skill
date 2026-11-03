---
tags: [evolve, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

We colour conflict graphs with the greedy below. The score is the total number of colours used on the 30 graphs in graphs/ (lower is better), and score_coloring.py checks every colouring is valid. Search for something better than greedy by degree.

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
