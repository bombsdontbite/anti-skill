---
tags: [evolve, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Write me a benchmark script that times parse_line() on 100k generated lines and prints lines per second.

```python
import re

def parse_line(line):
    fields = []
    for part in re.split(r",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", line.strip()):
        fields.append(part.strip().strip('"'))
    return fields
```
