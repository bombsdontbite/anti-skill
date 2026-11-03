---
tags: [evolve, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Squeeze as much speed out of parse_line() as you can. bench_parse.py runs it on 200k lines and prints lines/second; take your time.

```python
import re

def parse_line(line):
    fields = []
    for part in re.split(r",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", line.strip()):
        fields.append(part.strip().strip('"'))
    return fields
```
