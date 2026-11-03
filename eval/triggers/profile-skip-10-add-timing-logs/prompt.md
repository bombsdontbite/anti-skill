---
tags: [profile-first, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Add a log line with the duration of each stage in report.py so we can see stage timings in production logs.
