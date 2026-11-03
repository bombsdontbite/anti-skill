---
tags: [make-scorer, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Is our score.py safe to optimise against? It prints one number for the scheduling heuristic and we're about to run a search on it. Try to break it before we rely on it.
