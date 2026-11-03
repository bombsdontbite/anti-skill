---
tags: [bench-fairly, should-not-trigger, cross-profile-first]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

build_index.py takes three minutes on the full catalogue. Where does the time go?
