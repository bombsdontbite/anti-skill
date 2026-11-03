---
tags: [profile-first, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Where does our CLI's startup time go? `python -m mytool --help` takes 2.4 seconds before it prints anything.
