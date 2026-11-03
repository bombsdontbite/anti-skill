---
tags: [bench-fairly, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Since we upgraded pandas from 2.2 to 3.0 our nightly report (make_report.py) seems slower. Is that a real regression or just noise?
