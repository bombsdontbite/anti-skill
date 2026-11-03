---
tags: [make-scorer, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Our delivery route planner (routes.py) uses nearest neighbour. I want to improve it, but we've never measured how good it is. Set up a way to score it honestly, on instances we don't tune on.
