---
tags: [evolve, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

tokenize() passes 412 of the 450 cases in tests/test_tokenize.py, and the pass count is the only thing that matters. Try a few genuinely different approaches and keep whichever passes the most; I don't want a pile of special-case patches on the current one.
