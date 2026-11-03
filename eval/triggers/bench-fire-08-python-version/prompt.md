---
tags: [bench-fairly, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Is etl.py measurably faster on Python 3.14 than on 3.12? `python3.12 etl.py sample.csv` vs `python3.14 etl.py sample.csv`.
