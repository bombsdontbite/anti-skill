---
tags: [profile-first, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

etl.py chews through 500k rows in about three minutes. That feels way too slow for what it does. Why?
