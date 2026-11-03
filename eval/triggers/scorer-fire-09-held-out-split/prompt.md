---
tags: [make-scorer, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Set up a scoring script and a held-out split for our search ranking function (ranker.py, labelled queries in queries.jsonl), so an improvement on the queries we look at can be checked on queries nobody tuned on.
