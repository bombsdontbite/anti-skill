---
tags: [evolve, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Get our scheduler's score up. `python score.py --instances test/` prints one number, higher is better, and the current greedy heuristic gets 0.71. Find the best heuristic you can.
