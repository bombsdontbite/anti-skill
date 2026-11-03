---
tags: [make-scorer, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

I'm about to let an optimisation loop run against this benchmark for parse_line(). Can it be gamed?

```python
import time
from parse import parse_line

lines = [f'{i},"name {i}",x,{i * 3}' for i in range(200_000)]
start = time.perf_counter()
for line in lines:
    parse_line(line)
print(f"{len(lines) / (time.perf_counter() - start):.0f}")
```
