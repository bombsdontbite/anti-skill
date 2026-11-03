---
tags: [evolve, should-trigger]
plugins: [../../../plugins/anti-skill]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Skill, Read, Glob, Grep]
---

Let's do an autoresearch-style loop: train.py does a 5-minute training run and prints val_bpb at the end. Iterate on the model and optimizer code to get val_bpb as low as it will go.
