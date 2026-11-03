---
tags: [bench-fairly, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Give me a speedup number for my PR description: `python solve_old.py in.txt` versus `python solve_new.py in.txt`.
