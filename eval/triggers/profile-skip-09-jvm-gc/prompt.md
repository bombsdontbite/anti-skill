---
tags: [profile-first, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Our production Java service has 2-second GC pauses under load. Which JVM flags and GC settings should we look at?
