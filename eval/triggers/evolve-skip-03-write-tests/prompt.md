---
tags: [evolve, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Write pytest tests for parse_line(): empty lines, quoted fields with commas inside, trailing commas.

```python
import re

def parse_line(line):
    fields = []
    for part in re.split(r",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", line.strip()):
        fields.append(part.strip().strip('"'))
    return fields
```
