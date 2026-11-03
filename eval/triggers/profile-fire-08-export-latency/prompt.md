---
tags: [profile-first, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

The handler behind /export (export.py, plain Python, no framework) takes 9 seconds to build the CSV for our biggest account. Work out where that time goes and bring it down.
