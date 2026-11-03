---
tags: [bench-fairly, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Compare the speed of the two dedup implementations, the one in report.py and the one in report_v2.py. Which one wins on the 20k customers?
