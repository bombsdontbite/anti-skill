---
tags: [evolve, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Improve the compression ratio of encode() on the corpus in samples/. ratio.py reports bytes out over bytes in and checks the round trip. I'm after the best encoder you can come up with, not a single tweak.
