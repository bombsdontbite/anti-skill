---
tags: [bench-fairly, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Is our test suite faster with `pytest -n 4` than plain `pytest`? I want to know if it's worth turning on in CI.
