---
tags: [bench-fairly, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

We replaced json with orjson in export.py. Did it actually get faster? The old version is in export_old.py.
