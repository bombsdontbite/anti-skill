---
tags: [bench-fairly, should-not-trigger, cross-make-scorer]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Write a benchmark harness for tokenize() that an optimisation loop can use as its score. There isn't one yet, only the code and its tests.
