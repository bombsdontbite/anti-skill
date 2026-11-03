---
tags: [make-scorer, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Write a scoring function for our graph colouring heuristic, so we can point an optimisation loop at it. Right now there's only color() itself in coloring.py and a couple of tests.
