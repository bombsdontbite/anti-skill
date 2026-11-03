---
tags: [profile-first, should-not-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Why would this Postgres query be slow on a 50M-row table?

```sql
SELECT * FROM orders WHERE lower(email) = 'a@b.c' ORDER BY created_at DESC LIMIT 20;
```
