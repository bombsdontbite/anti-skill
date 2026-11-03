---
tags: [profile-first, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Figure out where the time goes when our CLI starts: `python -m mytool --help` takes almost three seconds.
