---
tags: [evolve, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Set up something like FunSearch for me: generate candidate priority functions for online bin packing, score each one with my evaluator (evaluate.py, prints the fraction of optimal), keep the best and iterate on them.
