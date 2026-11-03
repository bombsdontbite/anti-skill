---
tags: [evolve, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Our scheduler module has grown into one 900-line file. How would you split it up so it's easier to work on?
