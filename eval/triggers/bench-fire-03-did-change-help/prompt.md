---
tags: [bench-fairly, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

I swapped the regex in parse_line() for str.split and it feels faster. Did it actually get faster? The old version is parse_old.py, the new one is parse.py.
