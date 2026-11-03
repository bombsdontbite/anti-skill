---
tags: [make-scorer, should-not-trigger, cross-evolve]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

bench.py already times dedup() in report.py and asserts the result. Use it as the score and find the fastest dedup you can; try several genuinely different approaches.
