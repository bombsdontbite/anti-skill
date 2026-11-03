---
tags: [bench-fairly, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Does building our C parser with -O3 instead of -O2 make it any faster? `make parser CFLAGS=-O2` vs `-O3`, then `./parser big.json`.
