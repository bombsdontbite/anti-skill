---
type: llm
focus: last_message
---

The user pasted code that was not run. Judge only whether the reply rewrites it for speed.
PASS if the reply gives no changed version of the user's code meant to run faster. A script,
command or wrapper that only times or profiles the unchanged code passes.
FAIL if it gives modified code of the user's function or script presented as faster or as the fix.
