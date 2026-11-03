---
tags: [profile-first, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

In report.py, replace the list with a set in the duplicate check; the order of customers must be kept.
