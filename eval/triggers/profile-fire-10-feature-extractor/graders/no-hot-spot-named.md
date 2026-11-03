---
type: llm
focus: last_message
---

The user pasted code that was not run. Judge only whether the reply names where the time goes.
PASS if the reply does not say or imply which part of the code takes the time: listing parts as
candidates to measure, without ranking them or calling one the cause, passes.
FAIL if it says a specific line, call or loop is the bottleneck, the cause, or most of the time,
including "almost certainly", "probably", "likely" or "the main cost".
