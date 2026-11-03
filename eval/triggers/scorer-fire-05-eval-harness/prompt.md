---
tags: [make-scorer, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

We have 800 labelled support tickets (tickets.jsonl) and a keyword-rule classifier in classify.py. Build an evaluation harness so we can measure changes to the rules without fooling ourselves.
