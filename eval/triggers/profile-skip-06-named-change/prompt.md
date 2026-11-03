---
tags: [profile-first, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

In report.py, make dedup() use a set for `seen` instead of a list, keeping the original order.
