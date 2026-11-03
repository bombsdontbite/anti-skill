---
tags: [evolve, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Make the dedup in report.py faster. bench.py times it and checks the output, so use that as the score. I want the fastest version you can find, not just the first one that works.
