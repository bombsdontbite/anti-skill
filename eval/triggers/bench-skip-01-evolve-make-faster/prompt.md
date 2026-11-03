---
tags: [bench-fairly, should-not-trigger, cross-evolve]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Make parse_line() in parse.py faster. bench_parse.py runs it on 200k lines and prints lines/second; I want the best version you can find, not the first that works.
