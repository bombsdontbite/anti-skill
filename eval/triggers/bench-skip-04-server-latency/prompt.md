---
tags: [bench-fairly, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

What's the p99 latency of our API at 200 requests per second? It's running on localhost:8000.
