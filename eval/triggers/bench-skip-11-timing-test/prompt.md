---
tags: [bench-fairly, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

test_export is flaky because it asserts the export finishes in under 2 seconds. Make the test stop depending on timing.
