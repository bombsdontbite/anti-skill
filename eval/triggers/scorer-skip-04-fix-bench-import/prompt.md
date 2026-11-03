---
tags: [make-scorer, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

bench.py fails with ModuleNotFoundError: No module named 'report' when I run it from the parent folder. Fix that.
