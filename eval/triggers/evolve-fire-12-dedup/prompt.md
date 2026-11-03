---
tags: [evolve, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Make the dedup function in report.py as fast as possible. bench.py times it and checks the result, that's the score. I need the best version, not the first one that works.
