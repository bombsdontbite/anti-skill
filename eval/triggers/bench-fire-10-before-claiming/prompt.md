---
tags: [bench-fairly, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

I rewrote dedup() with a dict; my version is in report_new.py, the original in report.py. Before I tell the team it's faster, check that it really is.
