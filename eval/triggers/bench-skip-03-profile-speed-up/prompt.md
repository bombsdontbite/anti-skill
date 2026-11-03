---
tags: [bench-fairly, should-not-trigger, cross-profile-first]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Speed up export.py, it takes 9 seconds to build the CSV for our biggest account.
