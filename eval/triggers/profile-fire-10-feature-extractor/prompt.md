---
tags: [profile-first, should-trigger, pasted-code]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

This feature extractor is the slowest step of our nightly pipeline (about 11 minutes a night on 2M documents). Make it faster.

```python
import math

def extract(batch, vocab):
    out = []
    for doc in batch:
        words = doc.lower().split()
        vec = [0.0] * len(vocab)
        for w in words:
            if w in list(vocab):
                vec[list(vocab).index(w)] += 1
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        out.append([v / norm for v in vec])
    return out
```
